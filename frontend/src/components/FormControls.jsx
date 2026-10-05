import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription,
  AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from '@/components/ui/alert-dialog';

export const SelectField = ({ value, onChange, options, placeholder, testId, disabled, className }) => (
  <Select value={value || undefined} onValueChange={onChange} disabled={disabled}>
    <SelectTrigger data-testid={testId} className={className}>
      <SelectValue placeholder={placeholder} />
    </SelectTrigger>
    <SelectContent>
      {options.map((o) => (
        <SelectItem key={o.value} value={o.value} data-testid={`${testId}-option-${o.value}`}>
          {o.label}
        </SelectItem>
      ))}
    </SelectContent>
  </Select>
);

export const ConfirmDelete = ({ title, description, onConfirm, trigger, testId }) => (
  <AlertDialog>
    <AlertDialogTrigger asChild>{trigger}</AlertDialogTrigger>
    <AlertDialogContent data-testid={`${testId}-dialog`}>
      <AlertDialogHeader>
        <AlertDialogTitle className="font-display uppercase tracking-wide">{title}</AlertDialogTitle>
        <AlertDialogDescription>{description}</AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel data-testid={`${testId}-cancel`}>Cancel</AlertDialogCancel>
        <AlertDialogAction data-testid={`${testId}-confirm`} onClick={onConfirm} className="bg-red-600 text-white hover:bg-red-500">
          Delete
        </AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
);
