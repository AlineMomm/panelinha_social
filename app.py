from flask import Flask, render_template, redirect, url_for, flash, request
from config import Config
from models import db, User
from forms import LoginForm, RegisterForm
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from urllib.parse import urlparse

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # inicializa extensões
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.login_view = 'login'  # rota usada para redirecionar quando não autenticado
    login_manager.login_message = "Faça login para acessar esta página."
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # rota inicial
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    # registro
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        form = RegisterForm()
        if form.validate_on_submit():
            # checar existência de usuário/email
            existing = User.query.filter((User.username == form.username.data) | (User.email == form.email.data)).first()
            if existing:
                flash('Nome de usuário ou e-mail já cadastrado.', 'warning')
                return render_template('register.html', form=form)
            # criar usuário
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            # opcional: logar automaticamente após registro
            login_user(user)
            flash('Conta criada com sucesso. Você foi logado.', 'success')
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('dashboard')
            return redirect(next_page)
        return render_template('register.html', form=form)

    # login
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                flash('Logado com sucesso.', 'success')
                # tratar o parâmetro next com segurança
                next_page = request.args.get('next')
                if not next_page or url_parse(next_page).netloc != '':
                    next_page = url_for('dashboard')
                return redirect(next_page)
            flash('E-mail ou senha inválidos.', 'danger')
        return render_template('login.html', form=form)

    # dashboard protegido — exemplo de rota protegida
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html')

    # logout
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Você saiu da conta.', 'info')
        return redirect(url_for('login'))

    return app

if __name__ == '__main__':
    app = create_app()
    # cria banco se não existir
    with app.app_context():
        db.create_all()
    app.run(debug=True)
