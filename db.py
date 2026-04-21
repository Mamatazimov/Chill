import sqlite3


class DataBase:
    def __init__(self, path: str):
        self.connection = sqlite3.connect(path)

    def init_db(self):
        with self.connection as conn:
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS projects(
                           id INTEGER PRIMARY KEY,
                           path TEXT UNIQUE,
                           flow TEXT,
                           head_save INTEGER,
                           flow_data TEXT
                           )
                """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS blobs(
                           id INTEGER PRIMARY KEY,
                           hash TEXT UNIQUE
                           )
                """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS trees(
                           id INTEGER PRIMARY KEY,
                           hash TEXT UNIQUE,
                           tree TEXT
                           )
                """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS saves(
                           id INTEGER PRIMARY KEY,
                           project_id INTEGER,
                           tree_id INTEGER,
                           parent_id INTEGER,
                           comment TEXT,
                           time TEXT,
                           flow TEXT
                           )
                """)

    # modules of projects table

    def project_exists(self, path):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM projects WHERE path = ?", (path,))
            return cur.fetchone() is not None

    def create_project(self, path, flow="main", head_save=0, flow_data={}):
        flow_data[flow] = head_save
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO projects(path, flow, head_save, flow_data) VALUES (?, ?, ?, ?)",
                (path, flow, head_save, str(flow_data)),
            )

    def get_project_id(self, path):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, flow, head_save, flow_data FROM projects WHERE path = ?",
                (path,),
            )
            project_id = cur.fetchone()
            return project_id

    def get_project_by_id(self, id):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, path, flow, head_save, flow_data FROM projects WHERE id = ?",
                (id,),
            )
            project_id = cur.fetchone()
            return project_id

    def get_list_projects(self):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, path, flow, head_save FROM projects")
            projects_list = cur.fetchall()
            return projects_list

    def update_project_flow(self, project_id, flow):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute("UPDATE projects SET flow = ? WHERE id = ?", (flow, project_id))

    def update_project_head(self, project_id, head):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE projects SET head_save = ? WHERE id = ?", (head, project_id)
            )
            print(
                f"Project with this id [{project_id}]'s head changed to this save id [{head}]"
            )

    def update_project_flow_data(self, project_id, flow_data):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE projects SET flow_data = ? WHERE id = ?",
                (str(flow_data), project_id),
            )

    def delete_project(self, project_id: int):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM saves WHERE project_id = ?", (project_id,))
            cur.execute("DELETE FROM projects WHERE id = ?", (project_id,))

    # modules of blobs table

    def blob_exists(self, hash):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM blobs WHERE hash = ?", (hash,))
            return cur.fetchone() is not None

    def create_blob(self, hash):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO blobs(hash) VALUES (?)",
                (hash,),
            )

    def get_blob_id(self, hash):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM blobs WHERE hash = ?", (hash,))
            blob_id = cur.fetchone()[0]
            return blob_id

    def get_blob_by_id(self, id):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute("SELECT hash FROM blobs WHERE id = ?", (id,))
            blob = cur.fetchone()[0]
            return blob

    def get_list_blobs(self):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, hash FROM blobs")
            blobs_list = cur.fetchall()
            return blobs_list

    def delete_blob(self, blob_hash: str):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM blobs WHERE hash = ?", (blob_hash,))

    # modules of trees table

    def tree_exists(self, hash):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM trees WHERE hash = ?", (hash,))
            return cur.fetchone() is not None

    def create_tree(self, hash):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute("INSERT OR IGNORE INTO trees(hash) VALUES (?)", (hash,))

    def update_tree(self, hash, tree, tree_id):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE trees SET hash = ?, tree = ? WHERE id = ?",
                (hash, tree, tree_id),
            )

    def get_tree_id(self, hash):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM trees WHERE hash = ?", (hash,))
            tree_id = cur.fetchone()[0]
            return tree_id

    def get_tree_by_id(self, id):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, hash, tree FROM trees WHERE id = ?", (id,))
            tree: tuple = cur.fetchone()
            return tree

    def get_list_trees(self):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, hash, tree FROM trees")
            trees_list = cur.fetchall()
            return trees_list

    def delete_tree(self, tree_id: int):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM trees WHERE id = ?", (tree_id,))

    # modules of saves table

    def save_exists(self, project_id, tree_id, parent_id, comment, time, flow):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id FROM saves WHERE project_id = ? AND tree_id = ? AND parent_id = ?
                AND comment = ? AND time = ? AND flow = ?
            """,
                (project_id, tree_id, parent_id, comment, time, flow),
            )
            return cur.fetchone() is not None

    def create_save(self, project_id, tree_id, parent_id, comment, time, flow):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR IGNORE INTO saves(project_id, tree_id, parent_id, comment, time, flow)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (project_id, tree_id, parent_id, comment, time, flow),
            )

    def get_save_id(self, project_id, tree_id, parent_id, comment, time, flow):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id FROM saves WHERE project_id = ? AND tree_id = ? AND parent_id = ?
                AND comment = ? AND time = ? AND flow = ?
            """,
                (project_id, tree_id, parent_id, comment, time, flow),
            )
            save_id = cur.fetchone()
            return save_id

    def get_list_saves(self, id: int = -1):
        with self.connection as conn:
            cur = conn.cursor()
            if id == -1:
                cur.execute(
                    "SELECT id, project_id, tree_id, parent_id, comment, time, flow FROM saves"
                )
            else:
                cur.execute(
                    "SELECT id, project_id, tree_id, parent_id, comment, time, flow FROM saves WHERE project_id = ?",
                    (id,),
                )
            saves_list = cur.fetchall()
            return saves_list

    def delete_save(self, save_id: int):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM saves WHERE id = ?", (save_id,))

    def get_save_by_id(self, id):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, project_id, tree_id, parent_id, comment, time, flow FROM saves WHERE id = ?",
                (id,),
            )
            save = cur.fetchone()
            if save[3] is None:
                save[3] = -1
            return save

    def get_list_saves_by_project(self, project_id):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, project_id, tree_id, parent_id, comment, time, flow FROM saves WHERE project_id = ?",
                (project_id,),
            )
            saves_list = cur.fetchall()
            return saves_list

    def update_save_parent(self, save_id, parent_id):
        with self.connection as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE saves SET parent_id = ? WHERE id = ?",
                (parent_id, save_id),
            )

    def close(self):
        self.connection.close()
