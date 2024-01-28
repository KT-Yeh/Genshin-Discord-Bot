修改完 models.py 後，執行以下指令，自動產生 migration 檔案
```
alembic -c database/alembic/alembic.ini revision --autogenerate -m "描述您的變更"
```