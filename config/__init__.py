try:
    import pymysql

    # PyMySQL como driver MySQL local (Render usa Postgres, no lo necesita)
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
