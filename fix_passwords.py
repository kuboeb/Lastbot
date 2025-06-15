import asyncio
from werkzeug.security import generate_password_hash
from sqlalchemy import select
import sys
sys.path.append('/home/Lastbot')
from config import config
from database import db_manager, Admin, Operator

async def fix_passwords():
    await db_manager.connect()
    
    async with db_manager.get_session() as session:
        # Исправляем админа
        result = await session.execute(
            select(Admin).where(Admin.username == config.ADMIN_USERNAME)
        )
        admin = result.scalar_one_or_none()
        
        if admin:
            admin.password_hash = generate_password_hash(config.ADMIN_PASSWORD)
            print(f"Updated password for admin: {admin.username}")
        else:
            admin = Admin(
                username=config.ADMIN_USERNAME,
                password_hash=generate_password_hash(config.ADMIN_PASSWORD)
            )
            session.add(admin)
            print(f"Created admin: {config.ADMIN_USERNAME}")
        
        # Исправляем оператора
        result = await session.execute(
            select(Operator).where(Operator.username == config.OPERATOR_USERNAME)
        )
        operator = result.scalar_one_or_none()
        
        if operator:
            operator.password_hash = generate_password_hash(config.OPERATOR_PASSWORD)
            print(f"Updated password for operator: {operator.username}")
        else:
            operator = Operator(
                username=config.OPERATOR_USERNAME,
                password_hash=generate_password_hash(config.OPERATOR_PASSWORD)
            )
            session.add(operator)
            print(f"Created operator: {config.OPERATOR_USERNAME}")
        
        await session.commit()
        print("Passwords fixed successfully!")
    
    await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(fix_passwords())
