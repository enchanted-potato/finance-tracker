import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import {
  Form, FormField, FormItem, FormLabel, FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

const formSchema = z.object({
  name: z.string().min(1, 'Name is required'),
});

interface ItemCrudDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editItem: { id: number; name: string } | null;
  queryKey: readonly string[];
  onCreate: (name: string) => Promise<unknown>;
  onUpdate: (id: number, name: string) => Promise<unknown>;
  itemLabel: string;
}

export function ItemCrudDialog({
  open,
  onOpenChange,
  editItem,
  queryKey,
  onCreate,
  onUpdate,
  itemLabel,
}: ItemCrudDialogProps) {
  const queryClient = useQueryClient();
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { name: editItem?.name ?? '' },
  });

  // CRITICAL: reset form on every open with potentially new editItem (RESEARCH.md Pitfall 1)
  // Key on editItem?.id not editItem — prevents infinite re-render on object reference change
  useEffect(() => {
    if (open) {
      form.reset({ name: editItem?.name ?? '' });
    }
  }, [open, editItem?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const mutation = useMutation({
    mutationFn: (values: z.infer<typeof formSchema>) => {
      if (editItem) {
        return onUpdate(editItem.id, values.name);
      }
      return onCreate(values.name);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKey as string[] });
      toast.success(editItem ? `${itemLabel} updated.` : `${itemLabel} added.`);
      onOpenChange(false);
    },
    onError: () => {
      toast.error('Failed to save. Please try again.');
    },
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{editItem ? `Edit ${itemLabel}` : `Add ${itemLabel}`}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(values => mutation.mutate(values))}>
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <Input placeholder={`${itemLabel} name`} {...field} />
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter className="mt-4">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? 'Saving...' : 'Save'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
