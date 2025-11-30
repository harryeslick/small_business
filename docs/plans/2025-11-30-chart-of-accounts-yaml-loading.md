# Chart of Accounts YAML Loading Design

**Date:** 2025-11-30
**Status:** Approved
**Phase:** 1 (Data Models)

## Overview

Add YAML-based loading for ChartOfAccounts to simplify account setup and configuration. YAML will be the primary way to define charts of accounts in practice, as these structures rarely change once established.

## Design Decisions

### 1. Simplified Account Model

**Merge code and name fields:**
- Remove separate `code` field (previously `^[A-Z0-9\-]+$` pattern)
- Use single `name` field as human-readable identifier
- Remove `parent_code` field (no hierarchy support)

**Rationale:** Limited number of accounts makes separate code unnecessary. Natural naming is more intuitive and follows project's API design principle of human-readable identifiers.

### 2. Flat Structure (No Hierarchy)

**Remove parent-child relationships:**
- All accounts within an account type are siblings
- Maximum 1 level (account type only)
- Remove hierarchy validation logic

**Rationale:** Simplifies model and matches stated requirement of 2-layer maximum (account type → accounts).

### 3. YAML Structure

**Format:**
```yaml
- name: asset
  description: Resources owned by the business
  accounts:
    - name: Cash
      description: Physical cash and coins
    - name: Accounts Receivable
      description: Money owed to the business by customers

- name: liability
  description: Obligations owed by the business
  accounts:
    - name: Accounts Payable
      description: Money owed to suppliers

- name: equity
  description: Owner's stake in the business
  accounts:
    - name: Owner's Capital
      description: Initial and additional capital invested

- name: income
  description: Revenue earned by the business
  accounts:
    - name: Sales
      description: Revenue from product/service sales

- name: expense
  description: Costs incurred in operations
  accounts:
    - name: Supplies
      description: Operating supplies and materials
```

**Key characteristics:**
- List of account type blocks
- Account type `name` matches `AccountType` enum values exactly (lowercase)
- Each account type has optional `description`
- Each account has `name` (required) and `description` (optional)
- Flat list of accounts per type (no nesting)

## Implementation Plan

### Model Changes

**`Account` model:**
```python
class Account(BaseModel):
    """Individual account in the chart of accounts."""

    name: str = Field(min_length=1)  # Replaces 'code' and 'name'
    account_type: AccountType
    description: str = ""  # No longer has parent_code
```

**`ChartOfAccounts` model:**
- Remove `validate_structure` checks for parent codes and hierarchy depth
- Add validation for duplicate account names
- Remove `get_children()` method
- Remove `get_root_accounts()` method
- Update `get_account()` to use `name` parameter instead of `code`
- Add `get_accounts_by_type()` helper method

### New Loading Method

**`ChartOfAccounts.from_yaml()` class method:**
```python
@classmethod
def from_yaml(cls, yaml_path: Path | str) -> "ChartOfAccounts":
    """Load chart of accounts from YAML file.

    Args:
        yaml_path: Path to YAML file containing account structure

    Returns:
        ChartOfAccounts instance

    Raises:
        FileNotFoundError: If yaml_path does not exist
        yaml.YAMLError: If YAML syntax is invalid
        ValidationError: If account structure is invalid
    """
    import yaml

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    accounts = []
    for account_type_block in data:
        account_type = AccountType(account_type_block["name"])
        for account_data in account_type_block.get("accounts", []):
            accounts.append(Account(
                name=account_data["name"],
                account_type=account_type,
                description=account_data.get("description", "")
            ))

    return cls(accounts=accounts)
```

### Validation Updates

**Add to `ChartOfAccounts.validate_structure()`:**
```python
@model_validator(mode="after")
def validate_structure(self):
    """Validate account structure rules."""
    # Check for duplicate account names
    names = [acc.name for acc in self.accounts]
    duplicates = [name for name in names if names.count(name) > 1]
    if duplicates:
        raise ValueError(f"Duplicate account names found: {duplicates}")

    return self
```

**Remove:**
- Parent code existence validation
- Max 2-level hierarchy validation

### Dependencies

**Add to project:**
- `pyyaml` - YAML parsing (required dependency)
- Import `yaml` at top of module (not lazy import)

## Testing Strategy

**Test coverage:**
1. Load valid YAML file successfully
2. Handle invalid account type values (not in enum)
3. Detect duplicate account names
4. Handle missing required fields (`name`)
5. Verify description defaults to empty string when omitted
6. Verify FileNotFoundError for missing files
7. Verify yaml.YAMLError for malformed YAML

**Test data location:**
- Create example chart of accounts YAML in `tests/fixtures/`

## Migration Impact

**Breaking changes:**
- `Account.code` removed → use `Account.name`
- `Account.parent_code` removed → no hierarchy support
- `ChartOfAccounts.get_children()` removed
- `ChartOfAccounts.get_root_accounts()` removed
- `ChartOfAccounts.get_account()` parameter renamed `code` → `name`

**Migration path:**
Since this is Phase 1 (data models only) with minimal implementation, breaking changes are acceptable. No data migration needed as no persistent storage exists yet.

## Future Considerations

**Not in scope for this change:**
- Account hierarchy support (explicitly removed)
- YAML schema validation (rely on Pydantic validation)
- Multiple charts of accounts per business (single chart assumed)
- Account activation/deactivation (all loaded accounts are active)

**May add later if needed:**
- Account balance tracking (Phase 3: Financial Reporting)
- Default chart templates for common business types
- YAML export method (`to_yaml()`)
