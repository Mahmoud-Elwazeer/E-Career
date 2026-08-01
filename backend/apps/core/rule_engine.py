"""
Rule Engine for automated actions based on conditions.

This module provides:
- Rule evaluation engine with condition parsing
- Action execution for recommendations, alerts, flags, reminders, celebrations
- Priority-based rule ordering
"""

import structlog
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = structlog.get_logger()


class RuleEvaluationResult:
    """Result of rule evaluation."""
    
    def __init__(
        self,
        rule_id: str,
        rule_name: str,
        matched: bool,
        action_type: str,
        action_params: Dict[str, Any],
        context: Dict[str, Any],
        priority: int = 0,
    ):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.matched = matched
        self.action_type = action_type
        self.action_params = action_params
        self.context = context
        self.priority = priority
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'matched': self.matched,
            'action_type': self.action_type,
            'action_params': self.action_params,
            'context': self.context,
            'priority': self.priority,
        }


class ConditionEvaluator:
    """Evaluates condition trees against context data."""
    
    # Comparison operators
    COMPARISON_OPS = {
        'eq': lambda a, b: a == b,
        'ne': lambda a, b: a != b,
        'gt': lambda a, b: a > b,
        'gte': lambda a, b: a >= b,
        'lt': lambda a, b: a < b,
        'lte': lambda a, b: a <= b,
        'in': lambda a, b: a in b,
        'nin': lambda a, b: a not in b,
        'contains': lambda a, b: b in a if isinstance(a, (str, list)) else False,
        'icontains': lambda a, b: b.lower() in a.lower() if isinstance(a, str) else False,
        'startswith': lambda a, b: a.startswith(b) if isinstance(a, str) else False,
        'endswith': lambda a, b: a.endswith(b) if isinstance(a, str) else False,
        'exists': lambda a, b: (a is not None) == b,
        'isnull': lambda a, b: (a is None) == b,
    }
    
    def __init__(self, context: Dict[str, Any]):
        self.context = context
    
    def evaluate(self, condition: Dict[str, Any]) -> bool:
        """
        Evaluate a condition tree against context.
        
        Condition format:
        {
            'operator': 'ALL'|'ANY'|'NOT',
            'conditions': [...],  # For ALL/ANY/NOT
            'field': 'field_name',
            'operator': 'eq'|'gt'|'lt'|'in'|...,
            'value': 'value_to_compare'
        }
        """
        if not condition:
            return True
        
        # Get operator
        op = condition.get('operator', 'ALL')
        
        if op == 'NOT':
            # Negate the result of the single condition
            sub_condition = condition.get('conditions', [{}])[0] if condition.get('conditions') else {}
            return not self.evaluate(sub_condition)
        
        elif op == 'ALL':
            # All conditions must match
            conditions = condition.get('conditions', [])
            return all(self.evaluate(c) for c in conditions)
        
        elif op == 'ANY':
            # Any condition must match
            conditions = condition.get('conditions', [])
            return any(self.evaluate(c) for c in conditions)
        
        else:
            # Single condition with field, operator, value
            return self._evaluate_single_condition(condition)
    
    def _evaluate_single_condition(self, condition: Dict[str, Any]) -> bool:
        """Evaluate a single condition (field, operator, value)."""
        field = condition.get('field')
        op = condition.get('operator', 'eq')
        value = condition.get('value')
        
        # Get field value from context
        field_value = self._get_field_value(field)
        
        # Get comparison function
        compare = self.COMPARISON_OPS.get(op)
        if not compare:
            logger.warning("unknown_condition_operator", operator=op)
            return False
        
        return compare(field_value, value)
    
    def _get_field_value(self, field_path: str) -> Any:
        """Get value from context using dot notation."""
        if not field_path:
            return None
        
        parts = field_path.split('.')
        value = self.context
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list) and part.isdigit():
                idx = int(part)
                value = value[idx] if idx < len(value) else None
            else:
                # Try attribute access
                value = getattr(value, part, None)
            
            if value is None:
                break
        
        return value


class RuleEngine:
    """Main rule evaluation engine."""
    
    def __init__(self, context: Dict[str, Any] = None):
        self.context = context or {}
        self.results: List[RuleEvaluationResult] = []
    
    def evaluate_rules(self, rules: List[Any], stop_on_first: bool = False) -> List[RuleEvaluationResult]:
        """
        Evaluate a list of rules against context.
        
        Args:
            rules: List of Rule model instances
            stop_on_first: If True, stop after first matching rule
            
        Returns:
            List of evaluation results
        """
        self.results = []
        
        # Sort by priority (highest first)
        sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            if not rule.is_active:
                continue
            
            # Evaluate conditions
            evaluator = ConditionEvaluator(self.context)
            matched = evaluator.evaluate(rule.conditions)
            
            result = RuleEvaluationResult(
                rule_id=str(rule.uuid),
                rule_name=rule.name,
                matched=matched,
                action_type=rule.action_type,
                action_params=rule.action_params,
                context=self.context,
                priority=rule.priority,
            )
            
            self.results.append(result)
            
            if matched and stop_on_first:
                break
        
        return self.results
    
    def execute_actions(self) -> List[Dict[str, Any]]:
        """Execute actions for all matching rules."""
        executed = []
        
        for result in self.results:
            if not result.matched:
                continue
            
            action_result = self._execute_action(result)
            executed.append(action_result)
        
        return executed
    
    def _execute_action(self, result: RuleEvaluationResult) -> Dict[str, Any]:
        """Execute a single action based on action type."""
        action_type = result.action_type
        action_params = result.action_params
        
        # Build action response
        response = {
            'rule_id': result.rule_id,
            'rule_name': result.rule_name,
            'action_type': action_type,
            'executed': True,
            'timestamp': datetime.now().isoformat(),
        }
        
        # Execute based on action type
        if action_type == 'recommend':
            response['action'] = self._action_recommend(action_params)
        elif action_type == 'alert':
            response['action'] = self._action_alert(action_params)
        elif action_type == 'flag':
            response['action'] = self._action_flag(action_params)
        elif action_type == 'remind':
            response['action'] = self._action_remind(action_params)
        elif action_type == 'celebrate':
            response['action'] = self._action_celebrate(action_params)
        elif action_type == 'recommend_employer':
            response['action'] = self._action_recommend_employer(action_params)
        elif action_type == 'request_cv_update':
            response['action'] = self._action_request_cv_update(action_params)
        else:
            logger.warning("unknown_action_type", action_type=action_type)
            response['executed'] = False
            response['error'] = f"Unknown action type: {action_type}"
        
        return response
    
    def _action_recommend(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend action - suggest something to user."""
        return {
            'type': 'recommendation',
            'message': params.get('message', 'We recommend you consider this option.'),
            'target': params.get('target', 'job'),
            'target_id': params.get('target_id'),
        }
    
    def _action_alert(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Alert action - notify user of important information."""
        return {
            'type': 'alert',
            'severity': params.get('severity', 'info'),
            'message': params.get('message', 'Important information for you.'),
            'target': params.get('target', 'user'),
        }
    
    def _action_flag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Flag action - mark something for review."""
        return {
            'type': 'flag',
            'reason': params.get('reason', 'Flagged for review'),
            'target': params.get('target'),
            'target_id': params.get('target_id'),
        }
    
    def _action_remind(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remind action - schedule a reminder."""
        return {
            'type': 'remind',
            'message': params.get('message', 'Don\'t forget to do this.'),
            'delay_hours': params.get('delay_hours', 24),
        }
    
    def _action_celebrate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Celebrate action - celebrate a milestone."""
        return {
            'type': 'celebration',
            'message': params.get('message', 'Congratulations on your achievement!'),
            'emoji': params.get('emoji', '🎉'),
        }
    
    def _action_recommend_employer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend to employer action."""
        return {
            'type': 'employer_recommendation',
            'candidate_id': params.get('candidate_id'),
            'job_id': params.get('job_id'),
            'match_score': params.get('match_score'),
            'reason': params.get('reason', 'Strong match based on skills and experience'),
        }
    
    def _action_request_cv_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Request CV update action."""
        return {
            'type': 'cv_update_request',
            'message': params.get('message', 'Your CV is outdated. Please update it.'),
            'days_since_last_update': params.get('days_since_last_update', 180),
        }


# ============================================================================
# Rule Seed Data (Week 13)
# ============================================================================

SEED_RULES = [
    {
        'name': 'Flag Low-Quality Jobs',
        'description': 'Flag jobs with trust_score below 0.4 for admin review',
        'category': 'job',
        'conditions': {
            'operator': 'ALL',
            'conditions': [
                {'field': 'job.trust_score', 'operator': 'lt', 'value': 0.4},
                {'field': 'job.is_flagged', 'operator': 'eq', 'value': False},
            ],
        },
        'action_type': 'flag',
        'action_params': {
            'reason': 'Low trust score indicates potential scam or low-quality posting',
            'target': 'job',
        },
        'is_active': True,
        'priority': 100,
    },
    {
        'name': 'Expire Stale Jobs',
        'description': 'Auto-expire jobs that are 30+ days old with 3+ failures',
        'category': 'job',
        'conditions': {
            'operator': 'ALL',
            'conditions': [
                {'field': 'job.age_days', 'operator': 'gte', 'value': 30},
                {'field': 'job.failure_count', 'operator': 'gte', 'value': 3},
                {'field': 'job.is_expired', 'operator': 'eq', 'value': False},
            ],
        },
        'action_type': 'alert',
        'action_params': {
            'message': 'Job has expired due to age and repeated failures',
            'target': 'job',
        },
        'is_active': True,
        'priority': 90,
    },
    {
        'name': 'Send Job Alert',
        'description': 'Send alert when job match meets minimum score threshold',
        'category': 'notification',
        'conditions': {
            'operator': 'ALL',
            'conditions': [
                {'field': 'match_score', 'operator': 'gte', 'value': 0.7},
                {'field': 'user.alert_frequency', 'operator': 'in', 'value': ['instant', 'daily']},
            ],
        },
        'action_type': 'alert',
        'action_params': {
            'message': 'New job match found!',
            'target': 'user',
        },
        'is_active': True,
        'priority': 80,
    },
    {
        'name': 'Recommend to Employer',
        'description': 'Recommend candidate to employer when career_score >= 85 and skill_match >= 90',
        'category': 'employer',
        'conditions': {
            'operator': 'ALL',
            'conditions': [
                {'field': 'candidate.career_score', 'operator': 'gte', 'value': 0.85},
                {'field': 'candidate.skill_match', 'operator': 'gte', 'value': 0.9},
            ],
        },
        'action_type': 'recommend_employer',
        'action_params': {
            'reason': 'Excellent match - highly recommended',
        },
        'is_active': True,
        'priority': 70,
    },
    {
        'name': 'Request CV Update',
        'description': 'Request CV update when CV is older than 180 days',
        'category': 'user',
        'conditions': {
            'operator': 'ALL',
            'conditions': [
                {'field': 'cv_age_days', 'operator': 'gte', 'value': 180},
            ],
        },
        'action_type': 'request_cv_update',
        'action_params': {
            'message': 'Your CV is outdated. Please update it to improve your match quality.',
            'days_since_last_update': 180,
        },
        'is_active': True,
        'priority': 60,
    },
    {
        'name': 'Celebrate New Certification',
        'description': 'Celebrate when user earns a new certification',
        'category': 'celebration',
        'conditions': {
            'operator': 'ALL',
            'conditions': [
                {'field': 'event', 'operator': 'eq', 'value': 'certification_earned'},
            ],
        },
        'action_type': 'celebrate',
        'action_params': {
            'message': 'Congratulations on earning your new certification! 🎓',
            'emoji': '🎓',
        },
        'is_active': True,
        'priority': 50,
    },
    {
        'name': 'Celebrate Score Improvement',
        'description': 'Celebrate when career score improves by 10+ points',
        'category': 'celebration',
        'conditions': {
            'operator': 'ALL',
            'conditions': [
                {'field': 'score_improvement', 'operator': 'gte', 'value': 0.1},
            ],
        },
        'action_type': 'celebrate',
        'action_params': {
            'message': 'Great job! Your career score improved by {improvement}%! 🚀',
            'emoji': '🚀',
        },
        'is_active': True,
        'priority': 40,
    },
]


def get_seed_rules() -> List[Dict[str, Any]]:
    """Get the seed rules for initial setup."""
    return SEED_RULES.copy()


def get_rule_by_category(category: str) -> List[Dict[str, Any]]:
    """Get rules for a specific category."""
    return [r for r in SEED_RULES if r['category'] == category]