import pymysql.cursors #Utilizamos un cursos para interactuar con BD
class MySQLConnection: #Clase que permite generar instancia de conexión con BD
   def __init__(self, db):
       self.db = db
   #El método que se encarga de la consulta
   def query_db(self, query, data=None):
       connection = pymysql.connect(host = 'localhost',
                                   user = 'root', # Cambia el usuario y contraseña
                                   password = 'root',
                                   db = self.db,
                                   charset = 'utf8mb4',
                                   cursorclass = pymysql.cursors.DictCursor,
                                   autocommit = True)
       with connection.cursor() as cursor:
           try:
               consulta = cursor.mogrify(query, data)
               print("Running Query:", consulta)
               executable = cursor.execute(query, data)
               if consulta.lower().find("insert") >= 0:
                   # La consulta INSERT regresan el id del nuevo registro
                   connection.commit()
                   return cursor.lastrowid
               elif consulta.lower().find("select") >= 0:
                   # La consulta SELECT regresa una LISTA DE DICCIONARIOS con los datos
                   result = cursor.fetchall()
                   return result
               else:
                   # UPDATE y DELETE no regresan nada
                   connection.commit()
           except Exception as e:
               # En caso de alguna falla, regresa FALSE
               print("Something went wrong", e)
               return False
           finally:
               # Cerramos conexión
               connection.close()
# connectToMySQL recibe el nombre de la base de datos y genera una instancia de MySQLConnection
def connectToMySQL(db):
   return MySQLConnection(db)