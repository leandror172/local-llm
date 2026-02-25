---
id: python-07-pytest-fixtures
domain: python
difficulty: medium
timeout: 300
description: pytest fixture suite with parametrize and async testing
---

Write a comprehensive pytest test suite for a `BankAccount` class (implementation assumed):
```python
class BankAccount:
    def __init__(self, owner: str, initial_balance: float = 0.0): ...
    def deposit(self, amount: float) -> float: ...
    def withdraw(self, amount: float) -> float: ...  # raises InsufficientFunds
    def transfer(self, target: BankAccount, amount: float) -> None: ...
    @property
    def balance(self) -> float: ...
    @property
    def transaction_history(self) -> list[dict]: ...
```

Write `conftest.py` with fixtures: `empty_account`, `funded_account` ($1000), `account_pair` (2×$500), `mock_time`

Write `test_bank_account.py` with:
- `@pytest.mark.parametrize` for deposit/withdraw (5 valid cases each)
- Parametrize for invalid amounts (negative, zero)
- `InsufficientFunds` test with message inspection
- Concurrent transfers test (10 threads × 10 transfers)
- Async test with `@pytest.mark.asyncio`

Requirements: `yield` fixtures, `pytest.raises`, `pytest.param(..., id="name")`
