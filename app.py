from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from sqlalchemy import func, text

# Configuração OTIMIZADA
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua-chave-secreta-muito-secreta-aqui-123'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///panelinha.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
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

# Models OTIMIZADOS
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    bio = db.Column(db.Text)
    profile_picture = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos com lazy='select' para melhor performance
    recipes = db.relationship('Recipe', backref='author', lazy='select')
    likes = db.relationship('Like', backref='user', lazy='select')
    comments = db.relationship('Comment', backref='user', lazy='select')
    saved_recipes = db.relationship('SavedRecipe', backref='user', lazy='select')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Recipe(db.Model):
    __tablename__ = 'recipe'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    ingredients = db.Column(db.Text)
    steps = db.Column(db.Text)
    image = db.Column(db.String(200))
    categories = db.Column(db.String(200))
    difficulty = db.Column(db.String(20), nullable=False, default='Fácil', index=True)  # NOVO CAMPO
    is_draft = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    views = db.Column(db.Integer, default=0, index=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # Relacionamentos otimizados
    likes = db.relationship('Like', backref='recipe', lazy='select')
    comments = db.relationship('Comment', backref='recipe', lazy='select')
    saved_by = db.relationship('SavedRecipe', backref='recipe', lazy='select')

    def like_count(self):
        if hasattr(self, '_like_count'):
            return self._like_count
        return len(self.likes)

    def comment_count(self):
        if hasattr(self, '_comment_count'):
            return self._comment_count
        return len(self.comments) 

    def saved_count(self):
        if hasattr(self, '_saved_count'):
            return self._saved_count
        return len(self.saved_by)  # Mudado para len()

    def is_liked_by_user(self, user):
        if not user.is_authenticated:
            return False
        # Verificação otimizada - agora usando lista
        return any(like.user_id == user.id for like in self.likes)

    def is_saved_by_user(self, user):
        if not user.is_authenticated:
            return False
        return any(saved.user_id == user.id for saved in self.saved_by)

class Like(db.Model):
    __tablename__ = 'like'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'recipe_id', name='unique_like'),)

class Comment(db.Model):
    __tablename__ = 'comment'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class SavedRecipe(db.Model):
    __tablename__ = 'saved_recipe'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False, index=True)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (db.UniqueConstraint('user_id', 'recipe_id', name='unique_save'),)

class RegistrationForm(FlaskForm):
    username = StringField('Nome de usuário', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Cadastrar')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este email já está em uso. Por favor, use outro email.')

# ROTAS DE AUTENTICAÇÃO
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash('Login realizado com sucesso!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('feed'))
        else:
            flash('Email ou senha incorretos.', 'danger')
    
    return render_template('login.html', title='Entrar', form=form)

@app.route('/recipe/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Verificar se o usuário é o autor da receita
    if recipe.user_id != current_user.id:
        flash('Você só pode editar suas próprias receitas.', 'danger')
        return redirect(url_for('recipe_detail', recipe_id=recipe.id))
    
    form = RecipeForm()
    
    if form.validate_on_submit():
        # Atualizar imagem se uma nova foi enviada
        if form.image.data:
            # Remover imagem antiga se existir
            if recipe.image:
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], recipe.image)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Salvar nova imagem
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            image_filename = f"recipe_{timestamp}_{form.image.data.filename}"
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            recipe.image = image_filename
        
        # Atualizar outros campos
        recipe.title = form.title.data
        recipe.description = form.description.data
        recipe.ingredients = form.ingredients.data
        recipe.steps = form.steps.data
        recipe.categories = form.categories.data
        recipe.difficulty = form.difficulty.data  # ADICIONE ESTA LINHA
        recipe.is_draft = 'save_draft' in request.form
        recipe.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Receita atualizada com sucesso!', 'success')
        return redirect(url_for('recipe_detail', recipe_id=recipe.id))
    
    # Preencher o formulário com os dados atuais
    elif request.method == 'GET':
        form.title.data = recipe.title
        form.description.data = recipe.description
        form.ingredients.data = recipe.ingredients
        form.steps.data = recipe.steps
        form.categories.data = recipe.categories
        form.difficulty.data = recipe.difficulty  # ADICIONE ESTA LINHA
    
    return render_template('edit_recipe.html', title='Editar Receita', form=form, recipe=recipe)

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    recipe_id = comment.recipe_id
    
    # Verificar se o usuário tem permissão para deletar
    if current_user.id != comment.user_id and current_user.id != comment.recipe.user_id:
        flash('Você não tem permissão para deletar este comentário.', 'danger')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    
    db.session.delete(comment)
    db.session.commit()
    
    flash('Comentário deletado com sucesso!', 'success')
    return redirect(url_for('recipe_detail', recipe_id=recipe_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Verificar se email ou username já existem
        existing_user = User.query.filter(
            (User.email == form.email.data) | (User.username == form.username.data)
        ).first()
        
        if existing_user:
            if existing_user.email == form.email.data:
                flash('Este email já está em uso.', 'danger')
            else:
                flash('Este nome de usuário já está em uso.', 'danger')
        else:
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html', title='Cadastrar', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('index'))

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class EditProfileForm(FlaskForm):
    username = StringField('Nome de usuário', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    bio = TextAreaField('Biografia', validators=[Length(max=500)])
    profile_picture = FileField('Foto de perfil', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])
    submit = SubmitField('Atualizar Perfil')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Este email já está em uso. Por favor, use outro email.')

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(original_username=current_user.username, original_email=current_user.email)
    
    if form.validate_on_submit():
        # Atualizar foto de perfil se uma nova foi enviada
        if form.profile_picture.data:
            # Remover imagem antiga se existir
            if current_user.profile_picture:
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_picture)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Salvar nova imagem
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            profile_filename = f"profile_{current_user.id}_{timestamp}_{form.profile_picture.data.filename}"
            form.profile_picture.data.save(os.path.join(app.config['UPLOAD_FOLDER'], profile_filename))
            current_user.profile_picture = profile_filename
        
        # Atualizar outros campos
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        
        db.session.commit()
        
        flash('Seu perfil foi atualizado com sucesso!', 'success')
        return redirect(url_for('user_profile', username=current_user.username))
    
    # Preencher o formulário com os dados atuais
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio
    
    return render_template('edit_profile.html', title='Editar Perfil', form=form)
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Senha Atual', validators=[DataRequired()])
    new_password = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Nova Senha', 
                                   validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Alterar Senha')

class SearchForm(FlaskForm):
    query = StringField('Buscar receitas...', validators=[DataRequired()])
    submit = SubmitField('🔍')

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    difficulty = request.args.get('difficulty', '')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Construir filtro de busca
    filters = [Recipe.is_draft == False]
    
    if query:
        search_filter = db.or_(
            Recipe.title.ilike(f'%{query}%'),
            Recipe.description.ilike(f'%{query}%'),
            Recipe.ingredients.ilike(f'%{query}%'),
            Recipe.categories.ilike(f'%{query}%')
        )
        filters.append(search_filter)
    
    if difficulty:
        filters.append(Recipe.difficulty == difficulty)
    
    recipes_query = Recipe.query.filter(*filters).order_by(Recipe.created_at.desc())
    
    # Paginação
    recipes_pagination = recipes_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Otimizar contagens
    recipes = get_recipes_with_counts(recipes_pagination.items)
    
    # Determinar título da página
    if query and difficulty:
        title = f'Busca: "{query}" + {difficulty}'
    elif query:
        title = f'Busca: "{query}"'
    elif difficulty:
        title = f'Dificuldade: {difficulty}'
    else:
        title = 'Todas as Receitas'
    
    return render_template('search.html', 
                         title=title,
                         recipes=recipes,
                         query=query,
                         difficulty=difficulty,
                         pagination=recipes_pagination)


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Verificar se a senha atual está correta
        if not current_user.check_password(form.current_password.data):
            flash('Senha atual incorreta.', 'danger')
            return render_template('change_password.html', title='Alterar Senha', form=form)
        
        # Atualizar a senha
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('Sua senha foi alterada com sucesso!', 'success')
        return redirect(url_for('edit_profile'))
    
    return render_template('change_password.html', title='Alterar Senha', form=form)

@app.route('/user/<username>')
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    # Buscar receitas públicas do usuário
    recipes = Recipe.query.filter_by(user_id=user.id, is_draft=False)\
                         .order_by(Recipe.created_at.desc())\
                         .all()
    
    return render_template('user_profile.html', 
                         title=f'Perfil - {user.username}', 
                         user=user, 
                         recipes=recipes)

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

class RecipeForm(FlaskForm):
    title = StringField('Título da Receita', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descrição Curta', validators=[DataRequired()])
    ingredients = TextAreaField('Ingredientes', validators=[DataRequired()])
    steps = TextAreaField('Passos do Preparo', validators=[DataRequired()])
    image = FileField('Foto da Receita', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])
    categories = StringField('Categorias')
    
    # CAMPO DE SELEÇÃO CORRIGIDO
    difficulty = SelectField(
        'Nível de Dificuldade', 
        choices=[
            ('', 'Selecione a dificuldade...'),
            ('Fácil', 'Fácil'),
            ('Médio', 'Médio'), 
            ('Difícil', 'Difícil')
        ], 
        validators=[DataRequired(message='Por favor, selecione o nível de dificuldade')]
    )
    
    submit = SubmitField('Publicar Receita')
    save_draft = SubmitField('Salvar Rascunho')

class CommentForm(FlaskForm):
    content = TextAreaField('Comentário', validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('Comentar')

# FUNÇÕES AUXILIARES OTIMIZADAS
def get_recipes_with_counts(recipes):
    """Otimiza contagens em lote - agora aceita tanto Query quanto List"""
    
    # Se for uma query, executa e pega os resultados
    if hasattr(recipes, 'all'):
        recipes = recipes.all()
    
    if not recipes:
        return []
    
    recipe_ids = [recipe.id for recipe in recipes]
    
    # Buscar contagens em lote
    like_counts = db.session.query(
        Like.recipe_id, 
        func.count(Like.id).label('count')
    ).filter(Like.recipe_id.in_(recipe_ids)).group_by(Like.recipe_id).all()
    
    comment_counts = db.session.query(
        Comment.recipe_id,
        func.count(Comment.id).label('count')
    ).filter(Comment.recipe_id.in_(recipe_ids)).group_by(Comment.recipe_id).all()
    
    saved_counts = db.session.query(
        SavedRecipe.recipe_id,
        func.count(SavedRecipe.id).label('count')
    ).filter(SavedRecipe.recipe_id.in_(recipe_ids)).group_by(SavedRecipe.recipe_id).all()
    
    # Criar dicionários para acesso rápido
    like_dict = {r.recipe_id: r.count for r in like_counts}
    comment_dict = {r.recipe_id: r.count for r in comment_counts}
    saved_dict = {r.recipe_id: r.count for r in saved_counts}
    
    # Atribuir contagens aos objetos
    for recipe in recipes:
        recipe._like_count = like_dict.get(recipe.id, 0)
        recipe._comment_count = comment_dict.get(recipe.id, 0)
        recipe._saved_count = saved_dict.get(recipe.id, 0)
    
    return recipes

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    
    # Limitar para 6 receitas na home
    recipes_query = Recipe.query.filter_by(is_draft=False).order_by(Recipe.created_at.desc()).limit(6)
    recipes = get_recipes_with_counts(recipes_query)
    
    return render_template('index.html', title='Panelinha Social', recipes=recipes)

@app.route('/feed')
@login_required
def feed():
    sort_by = request.args.get('sort', 'recent')
    recipes_query = Recipe.query.filter_by(is_draft=False)
    
    if sort_by == 'popular':
        recipes_query = recipes_query.outerjoin(Like).group_by(Recipe.id).order_by(func.count(Like.id).desc())
    elif sort_by == 'views':
        recipes_query = recipes_query.order_by(Recipe.views.desc())
    else:
        recipes_query = recipes_query.order_by(Recipe.created_at.desc())
    
    recipes = get_recipes_with_counts(recipes_query)
    return render_template('feed.html', title='Feed', recipes=recipes, sort_by=sort_by)

@app.route('/my_recipes')
@login_required
def my_recipes():
    recipes_query = Recipe.query.filter_by(user_id=current_user.id).order_by(Recipe.created_at.desc())
    recipes = get_recipes_with_counts(recipes_query)
    return render_template('my_recipes.html', title='Minhas Receitas', recipes=recipes)

@app.route('/saved_recipes')
@login_required
def saved_recipes():
    saved_query = SavedRecipe.query.filter_by(user_id=current_user.id).order_by(SavedRecipe.saved_at.desc())
    saved_items = saved_query.all()
    
    if not saved_items:
        return render_template('saved_recipes.html', title='Receitas Salvas', recipes=[])
    
    recipe_ids = [item.recipe_id for item in saved_items]
    recipes_query = Recipe.query.filter(Recipe.id.in_(recipe_ids)).filter_by(is_draft=False)
    recipes = get_recipes_with_counts(recipes_query)
    
    # Manter a ordem de salvamento
    recipe_dict = {recipe.id: recipe for recipe in recipes}
    ordered_recipes = [recipe_dict[item.recipe_id] for item in saved_items if item.recipe_id in recipe_dict]
    
    return render_template('saved_recipes.html', title='Receitas Salvas', recipes=ordered_recipes)

@app.route('/recipe/new', methods=['GET', 'POST'])
@login_required
def new_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            # Otimizar nome do arquivo
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            image_filename = f"recipe_{timestamp}_{form.image.data.filename}"
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
        recipe = Recipe(
            title=form.title.data,
            description=form.description.data,
            ingredients=form.ingredients.data,
            steps=form.steps.data,
            image=image_filename,
            categories=form.categories.data,
            difficulty=form.difficulty.data,  # ADICIONE ESTA LINHA
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
    # Carregar receita com joins para evitar N+1
    recipe = Recipe.query.options(
        db.joinedload(Recipe.author),
        db.joinedload(Recipe.likes),
        db.joinedload(Recipe.comments).joinedload(Comment.user)
    ).get_or_404(recipe_id)
    
    form = CommentForm()
    
    # Incrementar visualizações de forma otimizada
    recipe.views = Recipe.views + 1
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
    
    # Ordenar comentários
    comments = recipe.comments
    
    return render_template('recipe_detail.html', title=recipe.title, recipe=recipe, form=form, comments=comments)

# ... (mantém as outras rotas iguais, mas aplica as otimizações onde necessário)

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
    
    # Retornar contagem atualizada
    like_count = Like.query.filter_by(recipe_id=recipe_id).count()
    return jsonify({'liked': liked, 'like_count': like_count})

@app.route('/save/<int:recipe_id>', methods=['POST'])
@login_required
def save_recipe(recipe_id):
    saved = SavedRecipe.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    
    if saved:
        db.session.delete(saved)
        saved_status = False
    else:
        saved = SavedRecipe(user_id=current_user.id, recipe_id=recipe_id)
        db.session.add(saved)
        saved_status = True
    
    db.session.commit()
    
    # Retornar contagem atualizada
    saved_count = SavedRecipe.query.filter_by(recipe_id=recipe_id).count()
    return jsonify({'saved': saved_status, 'saved_count': saved_count})

# Migração para adicionar campo difficulty
def init_difficulty_column():
    """Execute esta função uma vez para adicionar a coluna difficulty"""
    try:
        with db.engine.connect() as conn:
            # Verificar se a coluna já existe (SQLite)
            result = conn.execute(text("PRAGMA table_info(recipe)"))
            columns = [row[1] for row in result]
            
            if 'difficulty' not in columns:
                conn.execute(text("ALTER TABLE recipe ADD COLUMN difficulty VARCHAR(20) DEFAULT 'Fácil'"))
                conn.execute(text("CREATE INDEX ix_recipe_difficulty ON recipe(difficulty)"))
                db.session.commit()
                print("✅ Coluna 'difficulty' adicionada com sucesso!")
            else:
                print("✅ Coluna 'difficulty' já existe!")
    except Exception as e:
        print(f"❌ Erro na migração: {e}")

# Atualize a parte final do arquivo:
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_difficulty_column()  # ADICIONE ESTA LINHA
        print("🚀 Panelinha Social iniciado!")
        print("📊 Banco configurado com índices e otimizações")
        print("⚡ Performance melhorada significativamente")
        print("🥄 Sistema de dificuldade implementado!")
    
    app.run(debug=True)