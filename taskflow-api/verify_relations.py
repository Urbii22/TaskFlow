from uuid import uuid4

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.board import Board
from app.models.column import Column
from app.models.comment import Comment
from app.models.task import Task, TaskPriority
from app.models.user import Role, User


def main():
    s = SessionLocal()
    try:
        # 1) Datos base: 2 usuarios (owner, assignee)
        owner = User(email=f"owner_{uuid4().hex[:6]}@ex.com", password_hash="x", role=Role.USER)
        assignee = User(email=f"assignee_{uuid4().hex[:6]}@ex.com", password_hash="x", role=Role.USER)
        s.add_all([owner, assignee])
        s.commit()
        s.refresh(owner)
        s.refresh(assignee)

        # 2) Board del owner, 2 columnas desordenadas (position=2,1) para probar orden
        board = Board(name="Demo", owner_id=owner.id)
        s.add(board)
        s.commit()
        s.refresh(board)

        c2 = Column(name="Doing", position=2, board_id=board.id)
        c1 = Column(name="Todo", position=1, board_id=board.id)
        s.add_all([c2, c1])
        s.commit()

        # 3) Task en la columna 1, asignada a assignee, con 2 comments
        col1 = s.scalar(select(Column).where(Column.board_id==board.id, Column.position==1))
        task = Task(
            title="Tarea",
            priority=TaskPriority.MEDIUM,
            position=1,
            column_id=col1.id,
            assignee_id=assignee.id,
        )
        s.add(task)
        s.commit()
        s.refresh(task)

        s.add_all([
            Comment(text="Hola", task_id=task.id, author_id=owner.id),
            Comment(text="Que tal", task_id=task.id, author_id=assignee.id),
        ])
        s.commit()

        # Verificaciones
        s.refresh(owner)
        s.refresh(board)
        s.refresh(task)
        assert len(owner.boards) == 1, "owner.boards debe tener 1 board"
        positions = [c.position for c in board.columns]
        assert positions == [1,2], f"board.columns no viene ordenado por position: {positions}"
        assert task.assignee and task.assignee.id == assignee.id, "task.assignee no coincide"
        assert len(task.comments) == 2, "task.comments debería tener 2 comentarios"

        print("OK: Relaciones básicas (owner/board/columns/task/comments) verificadas.")

        # 4) Cascade delete al borrar board (debe borrar columns/tasks/comments)
        s.delete(board)
        s.commit()

        cnt_cols = s.scalar(select(func.count(Column.id)))
        cnt_tasks = s.scalar(select(func.count(Task.id)))
        cnt_comments = s.scalar(select(func.count(Comment.id)))
        assert cnt_cols == 0 and cnt_tasks == 0 and cnt_comments == 0, "Cascade al borrar board no eliminó hijos"

        print("OK: Cascade delete de board -> columns/tasks/comments verificado.")

        # 5) ondelete=SET NULL en assignee: crear nuevo board/column/task y borrar assignee
        new_board = Board(name="Demo2", owner_id=owner.id)
        s.add(new_board)
        s.commit()
        s.refresh(new_board)
        new_col = Column(name="Todo", position=1, board_id=new_board.id)
        s.add(new_col)
        s.commit()
        s.refresh(new_col)
        t2 = Task(title="Tarea2", priority=TaskPriority.LOW, position=1, column_id=new_col.id, assignee_id=assignee.id)
        s.add(t2)
        s.commit()
        s.refresh(t2)

        s.delete(assignee)
        s.commit()
        t2_refetched = s.get(Task, t2.id)
        assert t2_refetched is not None and t2_refetched.assignee_id is None, "SET NULL en assignee_id no aplicado"

        print("OK: ondelete=SET NULL en tasks.assignee_id verificado.")

        print("Todas las verificaciones pasaron correctamente.")
    finally:
        s.close()

if __name__ == "__main__":
    main()
