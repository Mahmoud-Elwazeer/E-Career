/**
 * Dynamic Application Form Fields Renderer
 *
 * Renders custom form fields defined by employers as JSON schema.
 * Field types: text, textarea, select, multiselect, yes_no, number, date, url
 */
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";

export interface FormField {
  id: string;
  type: 'text' | 'textarea' | 'select' | 'multiselect' | 'yes_no' | 'number' | 'date' | 'url';
  label: string;
  required: boolean;
  placeholder?: string;
  options?: string[];
  validation?: {
    min_length?: number;
    max_length?: number;
    pattern?: string;
  };
}

interface DynamicFormFieldsProps {
  fields: FormField[];
  values: Record<string, any>;
  onChange: (fieldId: string, value: any) => void;
  errors?: Record<string, string>;
}

export default function DynamicFormFields({ fields, values, onChange, errors }: DynamicFormFieldsProps) {
  if (!fields || fields.length === 0) return null;

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
        Additional Questions
      </h3>
      {fields.map((field) => (
        <div key={field.id} className="space-y-1.5">
          <Label htmlFor={field.id} className="text-sm">
            {field.label}
            {field.required && <span className="text-destructive ml-1">*</span>}
          </Label>

          {field.type === 'text' && (
            <Input
              id={field.id}
              value={values[field.id] || ''}
              onChange={(e) => onChange(field.id, e.target.value)}
              placeholder={field.placeholder}
              maxLength={field.validation?.max_length}
            />
          )}

          {field.type === 'textarea' && (
            <Textarea
              id={field.id}
              value={values[field.id] || ''}
              onChange={(e) => onChange(field.id, e.target.value)}
              placeholder={field.placeholder}
              className="min-h-[80px]"
              maxLength={field.validation?.max_length}
            />
          )}

          {field.type === 'number' && (
            <Input
              id={field.id}
              type="number"
              value={values[field.id] || ''}
              onChange={(e) => onChange(field.id, e.target.value)}
              placeholder={field.placeholder}
            />
          )}

          {field.type === 'date' && (
            <Input
              id={field.id}
              type="date"
              value={values[field.id] || ''}
              onChange={(e) => onChange(field.id, e.target.value)}
            />
          )}

          {field.type === 'url' && (
            <Input
              id={field.id}
              type="url"
              value={values[field.id] || ''}
              onChange={(e) => onChange(field.id, e.target.value)}
              placeholder={field.placeholder || 'https://'}
            />
          )}

          {field.type === 'select' && field.options && (
            <Select
              value={values[field.id] || ''}
              onValueChange={(val) => onChange(field.id, val)}
            >
              <SelectTrigger>
                <SelectValue placeholder={field.placeholder || 'Select...'} />
              </SelectTrigger>
              <SelectContent>
                {field.options.map((opt) => (
                  <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          {field.type === 'multiselect' && field.options && (
            <div className="space-y-2">
              {field.options.map((opt) => {
                const selected: string[] = values[field.id] || [];
                return (
                  <div key={opt} className="flex items-center gap-2">
                    <Checkbox
                      id={`${field.id}-${opt}`}
                      checked={selected.includes(opt)}
                      onCheckedChange={(checked) => {
                        const next = checked
                          ? [...selected, opt]
                          : selected.filter((s: string) => s !== opt);
                        onChange(field.id, next);
                      }}
                    />
                    <Label htmlFor={`${field.id}-${opt}`} className="text-sm font-normal">{opt}</Label>
                  </div>
                );
              })}
            </div>
          )}

          {field.type === 'yes_no' && (
            <div className="flex items-center gap-2">
              <Switch
                id={field.id}
                checked={values[field.id] === true}
                onCheckedChange={(checked) => onChange(field.id, checked)}
              />
              <Label htmlFor={field.id} className="text-sm font-normal">
                {values[field.id] === true ? 'Yes' : 'No'}
              </Label>
            </div>
          )}

          {errors?.[field.id] && (
            <p className="text-xs text-destructive">{errors[field.id]}</p>
          )}
        </div>
      ))}
    </div>
  );
}

export function validateDynamicFields(fields: FormField[], values: Record<string, any>): Record<string, string> {
  const errors: Record<string, string> = {};

  for (const field of fields) {
    const val = values[field.id];

    if (field.required) {
      if (val === undefined || val === null || val === '' || (Array.isArray(val) && val.length === 0)) {
        errors[field.id] = `${field.label} is required`;
        continue;
      }
    }

    if (val && field.validation) {
      if (field.validation.min_length && String(val).length < field.validation.min_length) {
        errors[field.id] = `Minimum ${field.validation.min_length} characters`;
      }
      if (field.validation.max_length && String(val).length > field.validation.max_length) {
        errors[field.id] = `Maximum ${field.validation.max_length} characters`;
      }
      if (field.validation.pattern && !new RegExp(field.validation.pattern).test(String(val))) {
        errors[field.id] = `Invalid format`;
      }
    }
  }

  return errors;
}
