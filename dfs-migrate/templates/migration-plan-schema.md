# Zero-Downtime Database Migration Schema (`templates/migration-plan-schema.md`)

Use this document schema to structure every production database migration plan.

```markdown
# 🗄️ Database Migration Plan: [Migration Name]

> **Target Database**: [MySQL 8.0+ / PostgreSQL 15+ / SQLite 3]
> **Migration Tool**: [golang-migrate / alembic / flyway / native SQL]
> **Safety Level**: [Zero-Downtime Expand/Contract / Online DDL]
> **Estimated Table Volume**: [Rows: ~X million / Size: ~Y GB]

---

## 1. 变更风险与锁分析 (Lock & Risk Assessment)
- **Lock Type**: [e.g. Metadata Lock / Shared Lock / In-place DDL with NO LOCK]
- **Algorithm**: [e.g. `ALGORITHM=INPLACE, LOCK=NONE` / `CONCURRENTLY`]
- **Replication Lag Impact**: [Expected replica delay in seconds]

---

## 2. 五步过渡阶梯 (The 5-Step Expand/Contract Ladder)

### Phase 1: Expand (向后兼容扩展)
- [ ] Add new column as nullable or with benign default:
  ```sql
  -- SQL Migration Up
  ALTER TABLE users ADD COLUMN email_v2 VARCHAR(255) NULL;
  ```
- [ ] Application deploy: Read from `email`, write to both `email` and `email_v2` (Dual Write).

### Phase 2: Backfill (批量异步回填)
- [ ] Run batched background script with sleep intervals to prevent IO spikes:
  ```sql
  UPDATE users SET email_v2 = email WHERE email_v2 IS NULL AND id BETWEEN ? AND ?;
  ```

### Phase 3: Switch Reads (切读新字段)
- [ ] Verify data parity (`COUNT(*)` and hash check between old and new columns).
- [ ] Application deploy: Read from `email_v2`, continue writing to both.

### Phase 4: Stop Writes to Old (停写旧字段)
- [ ] Application deploy: Only write to `email_v2`, ignore `email`.

### Phase 5: Contract (回收旧结构)
- [ ] Drop legacy column / constraint after 1 full sprint monitoring period:
  ```sql
  ALTER TABLE users DROP COLUMN email;
  ```

---

## 3. 回滚方案 (Rollback Procedure)
- **Phase 1-2 Rollback**: Drop new column (`ALTER TABLE users DROP COLUMN email_v2;`), revert dual-write code.
- **Phase 3-4 Rollback**: Toggle feature flag to read from legacy column `email`.
- **Phase 5 Rollback**: Restore from point-in-time recovery (PITR) backup.
```
