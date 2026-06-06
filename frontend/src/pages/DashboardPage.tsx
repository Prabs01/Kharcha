import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { getErrorMessage } from '../api/client'
import { createGroup, listGroups } from '../api/groups'

export function DashboardPage() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [error, setError] = useState('')

  const { data: groups = [], isLoading } = useQuery({
    queryKey: ['groups'],
    queryFn: listGroups,
  })

  const createMutation = useMutation({
    mutationFn: (groupName: string) => createGroup(groupName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] })
      setName('')
      setShowForm(false)
      setError('')
    },
    onError: (err) => setError(getErrorMessage(err)),
  })

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    createMutation.mutate(name.trim())
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Your groups</h1>
          <p className="page-subtitle">Split bills and track who owes what</p>
        </div>
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => setShowForm((v) => !v)}
        >
          {showForm ? 'Cancel' : '+ New group'}
        </button>
      </div>

      {showForm && (
        <form className="inline-form card" onSubmit={handleSubmit}>
          {error && <div className="alert alert-error">{error}</div>}
          <label className="field">
            <span>Group name</span>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Goa Trip, Roommates"
              required
              autoFocus
            />
          </label>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={createMutation.isPending}
          >
            {createMutation.isPending ? 'Creating…' : 'Create group'}
          </button>
        </form>
      )}

      {isLoading ? (
        <div className="page-loading">
          <div className="spinner" />
        </div>
      ) : groups.length === 0 ? (
        <div className="empty-state card">
          <div className="empty-icon">👥</div>
          <h2>No groups yet</h2>
          <p>Create a group to start tracking shared expenses.</p>
        </div>
      ) : (
        <div className="group-grid">
          {groups.map((group) => (
            <Link key={group.id} to={`/groups/${group.id}`} className="group-card card">
              <div className="group-card-icon">
                {group.name.charAt(0).toUpperCase()}
              </div>
              <div className="group-card-body">
                <h2>{group.name}</h2>
                <span className="group-card-link">View details →</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
