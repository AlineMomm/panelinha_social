from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# Configuração
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua-chave-secreta-muito-secreta-aqui-123'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///panelinha.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# Inicialização
app = Flask(__name__)
app.config.from_object(Config)

# Criar pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    bio = db.Column(db.Text)
    profile_picture = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    recipes = db.relationship('Recipe', backref='author', lazy='dynamic')
    likes = db.relationship('Like', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')
    saved_recipes = db.relationship('SavedRecipe', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    ingredients = db.Column(db.Text)
    steps = db.Column(db.Text)
    image = db.Column(db.String(200))
    categories = db.Column(db.String(200))
    is_draft = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Chave estrangeira
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relacionamentos
    likes = db.relationship('Like', backref='recipe', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='recipe', lazy='dynamic', cascade='all, delete-orphan')
    saved_by = db.relationship('SavedRecipe', backref='recipe', lazy='dynamic', cascade='all, delete-orphan')
    
    def like_count(self):
        return self.likes.count()
    
    def comment_count(self):
        return self.comments.count()
    
    def is_liked_by_user(self, user):
        if user.is_authenticated:
            return Like.query.filter_by(user_id=user.id, recipe_id=self.id).first() is not None
        return False
    
    def is_saved_by_user(self, user):
        if user.is_authenticated:
            return SavedRecipe.query.filter_by(user_id=user.id, recipe_id=self.id).first() is not None
        return False

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'recipe_id', name='unique_like'),)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SavedRecipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'recipe_id', name='unique_save'),)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar')

class RegistrationForm(FlaskForm):
    username = StringField('Nome de usuário', 
                          validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', 
                       validators=[DataRequired(), Email()])
    password = PasswordField('Senha', 
                            validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', 
                                    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Cadastrar')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este email já está cadastrado. Por favor, use outro email.')

class RecipeForm(FlaskForm):
    title = StringField('Título da Receita', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descrição Curta', validators=[DataRequired()])
    ingredients = TextAreaField('Ingredientes (um por linha)', validators=[DataRequired()])
    steps = TextAreaField('Passos do Preparo (um por linha)', validators=[DataRequired()])
    image = FileField('Foto da Receita', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Apenas imagens são permitidas!')])
    categories = StringField('Categorias (separadas por vírgula)')
    submit = SubmitField('Publicar Receita')
    save_draft = SubmitField('Salvar Rascunho')

class CommentForm(FlaskForm):
    content = TextAreaField('Comentário', validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('Comentar')

# Routes
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Panelinha Social - Home')

@app.route('/feed')
@login_required
def feed():
    sort_by = request.args.get('sort', 'recent')
    
    recipes = Recipe.query.filter_by(is_draft=False)
    
    if sort_by == 'popular':
        recipes = recipes.outerjoin(Like).group_by(Recipe.id).order_by(db.func.count(Like.id).desc())
    else:
        recipes = recipes.order_by(Recipe.created_at.desc())
    
    recipes = recipes.all()
    
    return render_template('feed.html', title='Feed', recipes=recipes, sort_by=sort_by)

@app.route('/recipe/new', methods=['GET', 'POST'])
@login_required
def new_recipe():
    form = RecipeForm()
    
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            image_filename = f"recipe_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{form.image.data.filename}"
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
        is_draft = 'save_draft' in request.form
        
        recipe = Recipe(
            title=form.title.data,
            description=form.description.data,
            ingredients=form.ingredients.data,
            steps=form.steps.data,
            image=image_filename,
            categories=form.categories.data,
            is_draft=is_draft,
            user_id=current_user.id
        )
        
        db.session.add(recipe)
        db.session.commit()
        
        if is_draft:
            flash('Receita salva como rascunho!', 'info')
        else:
            flash('Receita publicada com sucesso!', 'success')
        
        return redirect(url_for('feed'))
    
    return render_template('new_recipe.html', title='Nova Receita', form=form)

@app.route('/recipe/<int:recipe_id>', methods=['GET', 'POST'])
def recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    form = CommentForm()
    
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Por favor, faça login para comentar.', 'warning')
            return redirect(url_for('login'))
        
        comment = Comment(
            content=form.content.data,
            user_id=current_user.id,
            recipe_id=recipe.id
        )
        
        db.session.add(comment)
        db.session.commit()
        
        flash('Comentário adicionado com sucesso!', 'success')
        return redirect(url_for('recipe_detail', recipe_id=recipe.id))
    
    # Buscar comentários ordenados por data (mais recentes primeiro)
    comments = Comment.query.filter_by(recipe_id=recipe_id).order_by(Comment.created_at.desc()).all()
    
    return render_template('recipe_detail.html', title=recipe.title, recipe=recipe, form=form, comments=comments)

@app.route('/recipe/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Verificar se o usuário é o autor da receita
    if recipe.author != current_user:
        flash('Você não tem permissão para editar esta receita.', 'danger')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    
    form = RecipeForm()
    
    if form.validate_on_submit():
        # Atualizar imagem se uma nova foi enviada
        if form.image.data:
            # Remover imagem antiga se existir
            if recipe.image and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], recipe.image)):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], recipe.image))
            
            image_filename = f"recipe_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{form.image.data.filename}"
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            recipe.image = image_filename
        
        # Atualizar outros campos
        recipe.title = form.title.data
        recipe.description = form.description.data
        recipe.ingredients = form.ingredients.data
        recipe.steps = form.steps.data
        recipe.categories = form.categories.data
        recipe.updated_at = datetime.utcnow()
        
        # Se estava como rascunho e agora está publicando
        if recipe.is_draft and 'submit' in request.form:
            recipe.is_draft = False
            flash('Receita publicada com sucesso!', 'success')
        elif recipe.is_draft and 'save_draft' in request.form:
            flash('Rascunho atualizado com sucesso!', 'info')
        else:
            flash('Receita atualizada com sucesso!', 'success')
        
        db.session.commit()
        return redirect(url_for('recipe_detail', recipe_id=recipe.id))
    
    # Preencher o formulário com os dados atuais
    elif request.method == 'GET':
        form.title.data = recipe.title
        form.description.data = recipe.description
        form.ingredients.data = recipe.ingredients
        form.steps.data = recipe.steps
        form.categories.data = recipe.categories
    
    return render_template('edit_recipe.html', title='Editar Receita', form=form, recipe=recipe)

@app.route('/recipe/<int:recipe_id>/delete', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Verificar se o usuário é o autor da receita
    if recipe.author != current_user:
        flash('Você não tem permissão para excluir esta receita.', 'danger')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    
    # Remover imagem se existir
    if recipe.image and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], recipe.image)):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], recipe.image))
    
    db.session.delete(recipe)
    db.session.commit()
    
    flash('Receita excluída com sucesso!', 'success')
    return redirect(url_for('feed'))

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # Verificar se o usuário é o autor do comentário ou o autor da receita
    if comment.user_id != current_user.id and comment.recipe.author.id != current_user.id:
        flash('Você não tem permissão para excluir este comentário.', 'danger')
        return redirect(url_for('recipe_detail', recipe_id=comment.recipe_id))
    
    recipe_id = comment.recipe_id
    db.session.delete(comment)
    db.session.commit()
    
    flash('Comentário excluído com sucesso!', 'success')
    return redirect(url_for('recipe_detail', recipe_id=recipe_id))

@app.route('/my_recipes')
@login_required
def my_recipes():
    # Mostrar receitas do usuário (publicadas e rascunhos)
    recipes = Recipe.query.filter_by(user_id=current_user.id).order_by(Recipe.created_at.desc()).all()
    return render_template('my_recipes.html', title='Minhas Receitas', recipes=recipes)

@app.route('/like/<int:recipe_id>', methods=['POST'])
@login_required
def like_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    like = Like.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    
    if like:
        db.session.delete(like)
        db.session.commit()
        return {'liked': False, 'like_count': recipe.like_count()}
    else:
        like = Like(user_id=current_user.id, recipe_id=recipe_id)
        db.session.add(like)
        db.session.commit()
        return {'liked': True, 'like_count': recipe.like_count()}

@app.route('/save/<int:recipe_id>', methods=['POST'])
@login_required
def save_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    saved = SavedRecipe.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    
    if saved:
        db.session.delete(saved)
        db.session.commit()
        return {'saved': False}
    else:
        saved = SavedRecipe(user_id=current_user.id, recipe_id=recipe_id)
        db.session.add(saved)
        db.session.commit()
        return {'saved': True}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash('Login realizado com sucesso!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('feed'))
        else:
            flash('Login falhou. Verifique seu email e senha.', 'danger')
    
    return render_template('login.html', title='Login', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Conta criada com sucesso! Agora você pode fazer login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Cadastrar', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)