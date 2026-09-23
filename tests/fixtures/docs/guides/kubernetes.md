# Kubernetes Deployments

A Deployment manages a ReplicaSet and provides declarative updates for Pods.

## Rolling updates

When you change the Pod template, the Deployment performs a rolling update,
replacing old Pods with new ones gradually. Use `maxSurge` and
`maxUnavailable` to control how many Pods are created or taken down at once.

## Rollback

Run `kubectl rollout undo deployment/my-app` to revert to the previous revision.
