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
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Inicialização
app = Flask(__name__)
app.config.from_object(Config)

# Criar pasta de uploads
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    bio = db.Column(db.Text)
    profile_picture = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    recipes = db.relationship('Recipe', backref='author', lazy='dynamic')
    likes = db.relationship('Like', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')
    saved_recipes = db.relationship('SavedRecipe', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    views = db.Column(db.Integer, default=0)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    likes = db.relationship('Like', backref='recipe', lazy='dynamic')
    comments = db.relationship('Comment', backref='recipe', lazy='dynamic')
    saved_by = db.relationship('SavedRecipe', backref='recipe', lazy='dynamic')

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
    username = StringField('Nome de usuário', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Cadastrar')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nome de usuário já está em uso.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este email já está cadastrado.')

class RecipeForm(FlaskForm):
    title = StringField('Título da Receita', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descrição Curta', validators=[DataRequired()])
    ingredients = TextAreaField('Ingredientes (um por linha)', validators=[DataRequired()])
    steps = TextAreaField('Passos do Preparo (um por linha)', validators=[DataRequired()])
    image = FileField('Foto da Receita', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])
    categories = StringField('Categorias (separadas por vírgula)')
    submit = SubmitField('Publicar Receita')
    save_draft = SubmitField('Salvar Rascunho')

class CommentForm(FlaskForm):
    content = TextAreaField('Comentário', validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('Comentar')

# Routes
@app.route('/')
def index():
    # Mostrar algumas receitas públicas na página inicial
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    
    recipes = Recipe.query.filter_by(is_draft=False).order_by(Recipe.created_at.desc()).limit(6).all()
    return render_template('index.html', title='Panelinha Social', recipes=recipes)

@app.route('/feed')
@login_required
def feed():
    sort_by = request.args.get('sort', 'recent')
    recipes = Recipe.query.filter_by(is_draft=False)
    
    if sort_by == 'popular':
        from sqlalchemy import func
        recipes = recipes.outerjoin(Like).group_by(Recipe.id).order_by(func.count(Like.id).desc())
    elif sort_by == 'views':
        recipes = recipes.order_by(Recipe.views.desc())
    else:
        recipes = recipes.order_by(Recipe.created_at.desc())
    
    return render_template('feed.html', title='Feed', recipes=recipes.all(), sort_by=sort_by)

@app.route('/my_recipes')
@login_required
def my_recipes():
    recipes = Recipe.query.filter_by(user_id=current_user.id).order_by(Recipe.created_at.desc()).all()
    return render_template('my_recipes.html', title='Minhas Receitas', recipes=recipes)

@app.route('/saved_recipes')
@login_required
def saved_recipes():
    saved = SavedRecipe.query.filter_by(user_id=current_user.id).order_by(SavedRecipe.saved_at.desc()).all()
    recipes = [saved_item.recipe for saved_item in saved]
    return render_template('saved_recipes.html', title='Receitas Salvas', recipes=recipes)

@app.route('/recipe/new', methods=['GET', 'POST'])
@login_required
def new_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            image_filename = f"recipe_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{form.image.data.filename}"
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
        recipe = Recipe(
            title=form.title.data,
            description=form.description.data,
            ingredients=form.ingredients.data,
            steps=form.steps.data,
            image=image_filename,
            categories=form.categories.data,
            is_draft='save_draft' in request.form,
            user_id=current_user.id,
            views=0
        )
        db.session.add(recipe)
        db.session.commit()
        
        flash('Receita salva!' if recipe.is_draft else 'Receita publicada!', 'success')
        return redirect(url_for('feed'))
    
    return render_template('new_recipe.html', title='Nova Receita', form=form)

@app.route('/recipe/<int:recipe_id>', methods=['GET', 'POST'])
def recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    form = CommentForm()
    
    # CONTADOR DE VISUALIZAÇÕES
    recipe.views = (recipe.views or 0) + 1
    db.session.commit()
    
    if form.validate_on_submit() and current_user.is_authenticated:
        comment = Comment(
            content=form.content.data,
            user_id=current_user.id,
            recipe_id=recipe.id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comentário adicionado!', 'success')
        return redirect(url_for('recipe_detail', recipe_id=recipe.id))
    
    comments = Comment.query.filter_by(recipe_id=recipe_id).order_by(Comment.created_at.desc()).all()
    return render_template('recipe_detail.html', title=recipe.title, recipe=recipe, form=form, comments=comments)

@app.route('/recipe/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    if recipe.author != current_user:
        flash('Você não tem permissão para editar esta receita.', 'danger')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    
    form = RecipeForm()
    
    if form.validate_on_submit():
        if form.image.data:
            if recipe.image and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], recipe.image)):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], recipe.image))
            
            image_filename = f"recipe_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{form.image.data.filename}"
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            recipe.image = image_filename
        
        recipe.title = form.title.data
        recipe.description = form.description.data
        recipe.ingredients = form.ingredients.data
        recipe.steps = form.steps.data
        recipe.categories = form.categories.data
        recipe.updated_at = datetime.utcnow()
        
        if recipe.is_draft and 'submit' in request.form:
            recipe.is_draft = False
            flash('Receita publicada com sucesso!', 'success')
        elif recipe.is_draft and 'save_draft' in request.form:
            flash('Rascunho atualizado com sucesso!', 'info')
        else:
            flash('Receita atualizada com sucesso!', 'success')
        
        db.session.commit()
        return redirect(url_for('recipe_detail', recipe_id=recipe.id))
    
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
    
    if recipe.author != current_user:
        flash('Você não tem permissão para excluir esta receita.', 'danger')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    
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
    
    if comment.user_id != current_user.id and comment.recipe.author.id != current_user.id:
        flash('Você não tem permissão para excluir este comentário.', 'danger')
        return redirect(url_for('recipe_detail', recipe_id=comment.recipe_id))
    
    recipe_id = comment.recipe_id
    db.session.delete(comment)
    db.session.commit()
    
    flash('Comentário excluído com sucesso!', 'success')
    return redirect(url_for('recipe_detail', recipe_id=recipe_id))

@app.route('/like/<int:recipe_id>', methods=['POST'])
@login_required
def like_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    like = Like.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    
    if like:
        db.session.delete(like)
        liked = False
    else:
        like = Like(user_id=current_user.id, recipe_id=recipe_id)
        db.session.add(like)
        liked = True
    
    db.session.commit()
    return jsonify({'liked': liked, 'like_count': recipe.likes.count()})

@app.route('/save/<int:recipe_id>', methods=['POST'])
@login_required
def save_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    saved = SavedRecipe.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    
    if saved:
        db.session.delete(saved)
        saved_status = False
    else:
        saved = SavedRecipe(user_id=current_user.id, recipe_id=recipe_id)
        db.session.add(saved)
        saved_status = True
    
    db.session.commit()
    return jsonify({'saved': saved_status})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('feed'))
        flash('Email ou senha inválidos.', 'danger')
    
    return render_template('login.html', title='Login', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Conta criada com sucesso! Faça login.', 'success')
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
        print("✅ Panelinha Social iniciado com sucesso!")
        print("📊 Banco de dados criado")
        print("🚀 Servidor rodando em http://localhost:5000")
    app.run(debug=True)