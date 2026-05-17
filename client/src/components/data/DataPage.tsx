import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { ItemCrudDialog } from './ItemCrudDialog';
import { BalanceEntryForm } from './BalanceEntryForm';
import { HistoryTable } from './HistoryTable';
import type { HistoryDayDisplay } from './HistoryTable';

export interface DataPageConfig<TItem extends { id: number; name: string }> {
  title: string;
  queryKey: readonly string[];
  historyQueryKey: readonly string[];
  fetchItems: () => Promise<TItem[]>;
  fetchHistory: () => Promise<HistoryDayDisplay[]>;
  createItem: (name: string) => Promise<unknown>;
  updateItem: (id: number, name: string) => Promise<unknown>;
  deleteItem: (id: number) => Promise<unknown>;
  submitEntry: (body: { item_type_id: number; entry_date: string; balance: number }) => Promise<unknown>;
  itemLabel: string;
}

export function DataPage<TItem extends { id: number; name: string }>({
  config,
}: {
  config: DataPageConfig<TItem>;
}) {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editItem, setEditItem] = useState<TItem | null>(null);

  const { data: items = [], isPending, isError } = useQuery({
    queryKey: config.queryKey as string[],
    queryFn: config.fetchItems,
  });

  const { data: history = [] } = useQuery({
    queryKey: config.historyQueryKey as string[],
    queryFn: config.fetchHistory,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => config.deleteItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: config.queryKey as string[] });
      toast.success(`${config.itemLabel} deleted.`);
    },
    onError: () => toast.error('Failed to delete. Please try again.'),
  });

  function handleAdd() {
    setEditItem(null);
    setDialogOpen(true);
  }

  function handleEdit(item: TItem) {
    setEditItem(item);
    setDialogOpen(true);
  }

  if (isPending) {
    return <p className="text-muted-foreground text-sm">Loading...</p>;
  }

  if (isError) {
    return <p className="text-destructive text-sm">Failed to load data.</p>;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{config.title}</h1>
        <Button onClick={handleAdd}>Add {config.itemLabel}</Button>
      </div>

      {/* Item list */}
      <div className="space-y-2">
        {items.length === 0 && (
          <p className="text-muted-foreground text-sm">No {config.itemLabel}s yet.</p>
        )}
        {items.map(item => (
          <div key={item.id} className="flex items-center justify-between rounded-md border border-border p-3">
            <span>{item.name}</span>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => handleEdit(item)}>
                Edit
              </Button>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button size="sm" variant="destructive">Delete</Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete {config.itemLabel}?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This will permanently delete "{item.name}". This action cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={() => deleteMutation.mutate(item.id)}>
                      Delete
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </div>
        ))}
      </div>

      {/* Balance entry form */}
      <div className="rounded-md border border-border p-4">
        <h2 className="text-lg font-medium mb-4">Record Balance</h2>
        <BalanceEntryForm
          items={items}
          historyQueryKey={config.historyQueryKey}
          submitEntry={config.submitEntry}
          itemLabel={config.itemLabel}
        />
      </div>

      {/* Entry history */}
      <div>
        <h2 className="text-lg font-medium mb-4">Entry History</h2>
        <HistoryTable data={history} />
      </div>

      {/* CRUD dialog */}
      <ItemCrudDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        editItem={editItem}
        queryKey={config.queryKey}
        onCreate={config.createItem}
        onUpdate={config.updateItem}
        itemLabel={config.itemLabel}
      />
    </div>
  );
}
