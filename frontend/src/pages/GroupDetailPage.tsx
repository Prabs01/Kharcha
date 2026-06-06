import { useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import {
  getGroupBalances,
  getSuggestedSettlements,
  listSettlements,
  recordSettlement,
} from '../api/analytics'
import { getErrorMessage } from '../api/client'
import { createExpense, deleteExpense, listExpenses } from '../api/expenses'
import {
  addGroupMember,
  getGroup,
  listGroupMembers,
  removeGroupMember,
} from '../api/groups'
import { listUsers } from '../api/users'
import { CurrencyAmount } from '../components/CurrencyAmount'
import type { Expense, SplitMethod, SplitParticipant, User } from '../api/types'

type Tab = 'expenses' | 'members' | 'balances' | 'settlements'

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-NP', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

function userName(users: User[], id: number): string {
  return users.find((u) => u.id === id)?.name ?? `User #${id}`
}

export function GroupDetailPage() {
  const { groupId } = useParams<{ groupId: string }>()
  const id = Number(groupId)
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<Tab>('expenses')
  const [error, setError] = useState('')

  const { data: group, isLoading: groupLoading } = useQuery({
    queryKey: ['group', id],
    queryFn: () => getGroup(id),
    enabled: !Number.isNaN(id),
  })

  const { data: members = [] } = useQuery({
    queryKey: ['group-members', id],
    queryFn: () => listGroupMembers(id),
    enabled: !Number.isNaN(id),
  })

  const { data: allUsers = [] } = useQuery({
    queryKey: ['users'],
    queryFn: listUsers,
    enabled: tab === 'members',
  })

  const { data: expenses = [], isLoading: expensesLoading } = useQuery({
    queryKey: ['expenses', id],
    queryFn: () => listExpenses(id),
    enabled: !Number.isNaN(id),
  })

  const { data: balancesData } = useQuery({
    queryKey: ['balances', id],
    queryFn: () => getGroupBalances(id),
    enabled: !Number.isNaN(id) && (tab === 'balances' || tab === 'settlements'),
  })

  const { data: suggestedData } = useQuery({
    queryKey: ['suggested-settlements', id],
    queryFn: () => getSuggestedSettlements(id),
    enabled: !Number.isNaN(id) && tab === 'settlements',
  })

  const { data: settlementsData } = useQuery({
    queryKey: ['settlements', id],
    queryFn: () => listSettlements(id),
    enabled: !Number.isNaN(id) && tab === 'settlements',
  })

  const memberMap = useMemo(
    () => new Map(members.map((m) => [m.id, m])),
    [members],
  )

  if (groupLoading) {
    return (
      <div className="page-loading">
        <div className="spinner" />
      </div>
    )
  }

  if (!group) {
    return (
      <div className="page">
        <div className="empty-state card">
          <h2>Group not found</h2>
          <Link to="/" className="btn btn-primary">
            Back to groups
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <Link to="/" className="back-link">
            ← All groups
          </Link>
          <h1>{group.name}</h1>
        </div>
      </div>

      <div className="tabs">
        {(['expenses', 'members', 'balances', 'settlements'] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            className={`tab ${tab === t ? 'active' : ''}`}
            onClick={() => {
              setTab(t)
              setError('')
            }}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {tab === 'expenses' && (
        <ExpensesTab
          groupId={id}
          members={members}
          expenses={expenses}
          loading={expensesLoading}
          onError={setError}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['expenses', id] })
            queryClient.invalidateQueries({ queryKey: ['balances', id] })
            queryClient.invalidateQueries({ queryKey: ['suggested-settlements', id] })
            setError('')
          }}
        />
      )}

      {tab === 'members' && (
        <MembersTab
          groupId={id}
          members={members}
          allUsers={allUsers}
          onError={setError}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['group-members', id] })
            setError('')
          }}
        />
      )}

      {tab === 'balances' && (
        <BalancesTab balances={balancesData?.balances ?? []} memberMap={memberMap} />
      )}

      {tab === 'settlements' && (
        <SettlementsTab
          groupId={id}
          members={members}
          suggested={suggestedData?.settlements ?? []}
          recorded={settlementsData?.settlements ?? []}
          onError={setError}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['settlements', id] })
            queryClient.invalidateQueries({ queryKey: ['balances', id] })
            queryClient.invalidateQueries({ queryKey: ['suggested-settlements', id] })
            setError('')
          }}
        />
      )}
    </div>
  )
}

function ExpensesTab({
  groupId,
  members,
  expenses,
  loading,
  onError,
  onSuccess,
}: {
  groupId: number
  members: User[]
  expenses: Expense[]
  loading: boolean
  onError: (msg: string) => void
  onSuccess: () => void
}) {
  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState('')
  const [amount, setAmount] = useState('')
  const [paidBy, setPaidBy] = useState(members[0]?.id ?? 0)
  const [splitMethod, setSplitMethod] = useState<SplitMethod>('equal')
  const [participants, setParticipants] = useState<SplitParticipant[]>([])

  const createMutation = useMutation({
    mutationFn: () =>
      createExpense(groupId, {
        title: title.trim(),
        total_amount: parseFloat(amount),
        paid_by_user_id: paidBy,
        split_method: splitMethod,
        split_participants:
          splitMethod === 'equal' ? undefined : participants,
      }),
    onSuccess: () => {
      setTitle('')
      setAmount('')
      setShowForm(false)
      setSplitMethod('equal')
      setParticipants([])
      onSuccess()
    },
    onError: (err) => onError(getErrorMessage(err)),
  })

  const deleteMutation = useMutation({
    mutationFn: (expenseId: number) => deleteExpense(groupId, expenseId),
    onSuccess: onSuccess,
    onError: (err) => onError(getErrorMessage(err)),
  })

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    createMutation.mutate()
  }

  function initParticipants(method: SplitMethod) {
    if (method === 'equal') {
      setParticipants([])
      return
    }
    setParticipants(
      members.map((m) => ({
        user_id: m.id,
        ...(method === 'percentage'
          ? { percentage: Math.round((100 / members.length) * 100) / 100 }
          : { amount: 0 }),
      })),
    )
  }

  return (
    <>
      <div className="section-header">
        <h2>Expenses</h2>
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => setShowForm((v) => !v)}
          disabled={members.length === 0}
        >
          {showForm ? 'Cancel' : '+ Add expense'}
        </button>
      </div>

      {members.length === 0 && (
        <div className="alert alert-info">Add members before creating expenses.</div>
      )}

      {showForm && (
        <form className="card form-card" onSubmit={handleSubmit}>
          <div className="form-grid">
            <label className="field">
              <span>Title</span>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Dinner, Uber, etc."
                required
              />
            </label>
            <label className="field">
              <span>Amount</span>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                min="0"
                step="0.01"
                required
              />
            </label>
            <label className="field">
              <span>Paid by</span>
              <select
                value={paidBy}
                onChange={(e) => setPaidBy(Number(e.target.value))}
              >
                {members.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Split method</span>
              <select
                value={splitMethod}
                onChange={(e) => {
                  const method = e.target.value as SplitMethod
                  setSplitMethod(method)
                  initParticipants(method)
                }}
              >
                <option value="equal">Equal</option>
                <option value="exact">Exact amounts</option>
                <option value="percentage">Percentage</option>
              </select>
            </label>
          </div>

          {splitMethod !== 'equal' && (
            <div className="split-participants">
              <span className="field-label">Split details</span>
              {participants.map((p, i) => (
                <div key={p.user_id} className="split-row">
                  <span>{userName(members, p.user_id)}</span>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={splitMethod === 'exact' ? (p.amount ?? '') : (p.percentage ?? '')}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value) || 0
                      setParticipants((prev) =>
                        prev.map((item, idx) =>
                          idx === i
                            ? splitMethod === 'exact'
                              ? { ...item, amount: val }
                              : { ...item, percentage: val }
                            : item,
                        ),
                      )
                    }}
                    placeholder={splitMethod === 'exact' ? 'Amount' : '%'}
                  />
                </div>
              ))}
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={createMutation.isPending}
          >
            {createMutation.isPending ? 'Saving…' : 'Save expense'}
          </button>
        </form>
      )}

      {loading ? (
        <div className="page-loading">
          <div className="spinner" />
        </div>
      ) : expenses.length === 0 ? (
        <div className="empty-state card">
          <p>No expenses recorded yet.</p>
        </div>
      ) : (
        <div className="list">
          {expenses.map((expense) => (
            <div key={expense.id} className="list-item card">
              <div className="list-item-main">
                <strong>{expense.title}</strong>
                <span className="muted">{formatDate(expense.created_at)}</span>
              </div>
              <div className="list-item-meta">
                <CurrencyAmount amount={expense.total_amount} />
                <span className="muted">paid by {expense.paid_by_user.name}</span>
              </div>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => deleteMutation.mutate(expense.id)}
                disabled={deleteMutation.isPending}
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </>
  )
}

function MembersTab({
  groupId,
  members,
  allUsers,
  onError,
  onSuccess,
}: {
  groupId: number
  members: User[]
  allUsers: User[]
  onError: (msg: string) => void
  onSuccess: () => void
}) {
  const [selectedUserId, setSelectedUserId] = useState<number | ''>('')

  const memberIds = new Set(members.map((m) => m.id))
  const availableUsers = allUsers.filter((u) => !memberIds.has(u.id))

  const addMutation = useMutation({
    mutationFn: (userId: number) => addGroupMember(groupId, userId),
    onSuccess: () => {
      setSelectedUserId('')
      onSuccess()
    },
    onError: (err) => onError(getErrorMessage(err)),
  })

  const removeMutation = useMutation({
    mutationFn: (userId: number) => removeGroupMember(groupId, userId),
    onSuccess: onSuccess,
    onError: (err) => onError(getErrorMessage(err)),
  })

  return (
    <>
      <div className="section-header">
        <h2>Members</h2>
      </div>

      {availableUsers.length > 0 && (
        <div className="inline-form card">
          <select
            value={selectedUserId}
            onChange={(e) =>
              setSelectedUserId(e.target.value ? Number(e.target.value) : '')
            }
          >
            <option value="">Add a member…</option>
            {availableUsers.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name} ({u.email})
              </option>
            ))}
          </select>
          <button
            type="button"
            className="btn btn-primary"
            disabled={!selectedUserId || addMutation.isPending}
            onClick={() => selectedUserId && addMutation.mutate(selectedUserId)}
          >
            Add
          </button>
        </div>
      )}

      {members.length === 0 ? (
        <div className="empty-state card">
          <p>No members in this group yet.</p>
        </div>
      ) : (
        <div className="list">
          {members.map((member) => (
            <div key={member.id} className="list-item card">
              <div className="avatar">{member.name.charAt(0).toUpperCase()}</div>
              <div className="list-item-main">
                <strong>{member.name}</strong>
                <span className="muted">{member.email}</span>
              </div>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => removeMutation.mutate(member.id)}
                disabled={removeMutation.isPending}
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}
    </>
  )
}

function BalancesTab({
  balances,
  memberMap,
}: {
  balances: { user_id: number; balance: number }[]
  memberMap: Map<number, User>
}) {
  if (balances.length === 0) {
    return (
      <div className="empty-state card">
        <p>Add expenses to see balances.</p>
      </div>
    )
  }

  return (
    <>
      <div className="section-header">
        <h2>Balances</h2>
        <p className="muted">Positive = owed to them · Negative = they owe</p>
      </div>
      <div className="list">
        {balances.map((b) => {
          const name = memberMap.get(b.user_id)?.name ?? `User #${b.user_id}`
          const isPositive = b.balance > 0
          const isNegative = b.balance < 0
          return (
            <div key={b.user_id} className="list-item card balance-item">
              <div className="avatar">{name.charAt(0).toUpperCase()}</div>
              <strong>{name}</strong>
              <CurrencyAmount
                amount={b.balance}
                showPlus
                className={`balance-amount ${isPositive ? 'positive' : ''} ${isNegative ? 'negative' : ''}`}
              />
            </div>
          )
        })}
      </div>
    </>
  )
}

function SettlementsTab({
  groupId,
  members,
  suggested,
  recorded,
  onError,
  onSuccess,
}: {
  groupId: number
  members: User[]
  suggested: { from_user_id: number; to_user_id: number; amount: number }[]
  recorded: {
    id: number
    from_user_id: number
    to_user_id: number
    amount: number
    settled_at: string
  }[]
  onError: (msg: string) => void
  onSuccess: () => void
}) {
  const recordMutation = useMutation({
    mutationFn: (data: {
      from_user_id: number
      to_user_id: number
      amount: number
    }) => recordSettlement(groupId, data),
    onSuccess: onSuccess,
    onError: (err) => onError(getErrorMessage(err)),
  })

  return (
    <>
      <div className="section-header">
        <h2>Suggested settlements</h2>
      </div>

      {suggested.length === 0 ? (
        <div className="empty-state card">
          <p>Everyone is settled up!</p>
        </div>
      ) : (
        <div className="list">
          {suggested.map((s) => (
            <div
              key={`${s.from_user_id}-${s.to_user_id}`}
              className="list-item card"
            >
              <div className="settlement-text">
                <strong>{userName(members, s.from_user_id)}</strong>
                <span className="muted">pays</span>
                <strong>{userName(members, s.to_user_id)}</strong>
              </div>
              <CurrencyAmount amount={s.amount} />
              <button
                type="button"
                className="btn btn-accent btn-sm"
                disabled={recordMutation.isPending}
                onClick={() => recordMutation.mutate(s)}
              >
                Record
              </button>
            </div>
          ))}
        </div>
      )}

      {recorded.length > 0 && (
        <>
          <div className="section-header" style={{ marginTop: '2rem' }}>
            <h2>Recorded settlements</h2>
          </div>
          <div className="list">
            {recorded.map((s) => (
              <div key={s.id} className="list-item card">
                <div className="settlement-text">
                  <strong>{userName(members, s.from_user_id)}</strong>
                  <span className="muted">→</span>
                  <strong>{userName(members, s.to_user_id)}</strong>
                </div>
                <CurrencyAmount amount={s.amount} />
                <span className="muted">{formatDate(s.settled_at)}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </>
  )
}
