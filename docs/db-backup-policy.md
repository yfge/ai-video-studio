# Database Backup Policy

This repository does not track runtime SQL backup dumps.

## Scope

- Applies to ad-hoc SQL backups under `ai-pic-backend/backups/`.
- Backup files must be stored outside Git (OSS/object storage or secured ops storage).

## Backup Procedure

1. Export backup from the running environment.
2. Upload the dump to external storage with access control.
3. Record metadata in ops notes:
   - environment
   - dump timestamp (UTC)
   - database/schema version
   - storage location/key
   - operator

## Restore Procedure

1. Download the target dump from external storage.
2. Restore into a non-production database first.
3. Verify schema compatibility and key API paths.
4. Run migrations if required.
5. Restore production only after verification.

## Compliance

- Do not commit SQL backup dumps to this repository.
- Use `ai-pic-backend/backups/*.sql` ignore rule to prevent accidental commits.
