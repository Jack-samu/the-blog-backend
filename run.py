from app import create_app


app = create_app()


if __name__ == '__main__':
    app.run('0.0.0.0:8088', debug=True)