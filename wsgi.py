from server import app

if __name__ == "__main__":
    # Configurações para produção
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.run(host='0.0.0.0', port=10000) 