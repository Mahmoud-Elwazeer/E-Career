"""
Management command to index all jobs into pgvector.

This command:
1. Connects to pgvector
2. Creates the collection if it doesn't exist
3. Fetches all active jobs from the database
4. Generates embeddings using AWS Bedrock (Cohere)
5. Upserts vectors via pgvector
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.jobs.models import Job
from apps.vectors.service import get_vector_service


class Command(BaseCommand):
    help = 'Index all active jobs into pgvector'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of jobs to process in each batch'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Show what would be indexed without actually indexing'
        )
        parser.add_argument(
            '--collection',
            type=str,
            default='jobs',
            help='Collection to index into (jobs, users, skills)'
        )
    
    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        collection = options['collection']
        
        # Get vector service
        vector_service = get_vector_service()
        
        # Ensure collection exists
        if not dry_run:
            self.stdout.write(f"Ensuring collection '{collection}' exists...")
            vector_service.ensure_collections()
        
        # Get all active jobs
        jobs = Job.objects.filter(status='active')
        total_jobs = jobs.count()
        
        self.stdout.write(f"Found {total_jobs} active jobs to index")
        
        if dry_run:
            self.stdout.write("=== DRY RUN MODE ===")
            self.stdout.write(f"Would index {total_jobs} jobs into '{collection}' collection")
            return
        
        # Process in batches
        indexed_count = 0
        failed_count = 0
        
        for i in range(0, total_jobs, batch_size):
            batch = jobs[i:i + batch_size]
            
            try:
                # Prepare documents for indexing
                documents = []
                for job in batch:
                    # Create text content for embedding
                    content_parts = [
                        job.title or '',
                        job.description or '',
                        job.company.name if job.company else '',
                        job.location or '',
                    ]
                    content = ' '.join(filter(None, content_parts))
                    
                    documents.append({
                        'id': str(job.id),
                        'vector': None,  # Will be generated
                        'payload': {
                            'title': job.title,
                            'description': job.description,
                            'company': job.company.name if job.company else None,
                            'location': job.location,
                            'employment_type': job.employment_type,
                            'experience_level': job.experience_level,
                            'salary_min': str(job.salary_min) if job.salary_min else None,
                            'salary_max': str(job.salary_max) if job.salary_max else None,
                            'is_remote': job.work_arrangement == 'remote',
                            'created_at': job.created_at.isoformat() if job.created_at else None,
                        }
                    })
                
                # Generate embeddings for the batch
                texts = [doc['payload']['title'] + ' ' + doc['payload']['description'] for doc in documents]
                embeddings = vector_service.generate_embeddings(texts)
                
                # Update documents with embeddings
                for doc, embedding in zip(documents, embeddings):
                    doc['vector'] = embedding
                
                # Upsert into pgvector
                success = vector_service.vector_plugin.upsert(collection, documents)
                
                if success:
                    indexed_count += len(documents)
                    self.stdout.write(f"Indexed {indexed_count}/{total_jobs} jobs...")
                else:
                    failed_count += len(documents)
                    self.stdout.write(self.style.WARNING(f"Failed to index batch"))
                    
            except Exception as e:
                failed_count += len(batch)
                self.stdout.write(self.style.ERROR(f"Error indexing batch: {e}"))
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nIndexing complete! "
                f"Indexed: {indexed_count}, Failed: {failed_count}"
            )
        )