import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { format } from 'date-fns';
import { CalendarIcon } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Form, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';

// Zod v4: use error key (not required_error) for custom messages on missing values
const entrySchema = z.object({
  item_type_id: z.number({ error: 'Select an item' }),
  entry_date: z.date(),
  balance: z.number({ error: 'Enter a balance' }).nonnegative('Balance must be 0 or greater'),
});

type EntryValues = z.infer<typeof entrySchema>;

interface BalanceEntryFormProps {
  items: { id: number; name: string }[];
  historyQueryKey: readonly string[];
  submitEntry: (body: { item_type_id: number; entry_date: string; balance: number }) => Promise<unknown>;
  itemLabel: string;
}

export function BalanceEntryForm({ items, historyQueryKey, submitEntry, itemLabel }: BalanceEntryFormProps) {
  const queryClient = useQueryClient();
  const form = useForm<EntryValues>({
    resolver: zodResolver(entrySchema),
    defaultValues: { entry_date: new Date() },
  });

  const mutation = useMutation({
    mutationFn: (values: EntryValues) =>
      submitEntry({
        item_type_id: values.item_type_id,
        entry_date: format(values.entry_date, 'yyyy-MM-dd'),
        balance: values.balance,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: historyQueryKey as string[] });
      toast.success('Balance entry saved.');
      form.reset({ entry_date: new Date() });
    },
    onError: () => toast.error('Failed to save. Please try again.'),
  });

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(values => mutation.mutate(values))}
        className="space-y-4"
      >
        <FormField
          control={form.control}
          name="item_type_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Select {itemLabel}</FormLabel>
              <Select
                onValueChange={val => field.onChange(parseInt(val, 10))}
                value={field.value?.toString()}
              >
                <SelectTrigger>
                  <SelectValue placeholder={`Select ${itemLabel}...`} />
                </SelectTrigger>
                <SelectContent>
                  {items.map(item => (
                    <SelectItem key={item.id} value={item.id.toString()}>
                      {item.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="entry_date"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Date</FormLabel>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    type="button"
                    variant="outline"
                    className={cn(
                      'w-full justify-start text-left font-normal',
                      !field.value && 'text-muted-foreground'
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {field.value ? format(field.value, 'PPP') : 'Pick a date'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  {/* react-day-picker v10: initialFocus prop removed; focus handled automatically */}
                  <Calendar
                    mode="single"
                    selected={field.value}
                    onSelect={field.onChange}
                  />
                </PopoverContent>
              </Popover>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="balance"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Balance (£)</FormLabel>
              <Input
                type="number"
                step="0.01"
                min="0"
                placeholder="0.00"
                {...field}
                onChange={e => field.onChange(e.target.value === '' ? undefined : parseFloat(e.target.value))}
              />
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? 'Saving...' : 'Save Entry'}
        </Button>
      </form>
    </Form>
  );
}
