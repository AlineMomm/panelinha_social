# 🍳 Panelinha Social
Conectando Pessoas Pela Culinária!

## Sobre o Projeto
O **Panelinha Social** é uma plataforma web onde entusiastas da culinária podem compartilhar suas receitas, descobrir novas ideias culinárias e interagir com outros amantes da gastronomia. Desenvolvido com Flask, oferece uma experiência intuitiva e social para todos os tipos de cozinheiros (ou não cozinheiros).

### Objetivos
- Criar um hub centralizado para amantes da gastronomia
- Combinar rede social com organização de receitas
- Fomentar comunidade e troca de conhecimentos
- Facilitar descoberta de novas receitas

## Instalação
### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
### Passo a Passo
#### 1. Clone o repositório
git clone https://github.com/seu-usuario/panelinha-social.git
cd panelinha-social
#### 2. Crie um ambiente virtual (recomendado)
python -m venv venv
#### 3. Ative o ambiente virtual
##### (Windows:)                  
source venv/bin/activate
##### (Linux/Mac:)
venv\Scripts\activate
#### 4. Instale as dependências
pip install -r requirements.txt
#### 5. Execute a aplicação
python app.py
#### 6. Acesse no navegador

# Funcionalidades
## Gestão de Receitas
- Criar, editar e excluir receitas
- Sistema de rascunhos
- Upload de imagens
- Categorização por dificuldade
- Categorias personalizadas
- Ingredientes e modo de preparo organizados
- Modo impressão otimizado
## Sistema Social
- Curtir e salvar receitas
- Comentar em receitas
- Perfis de usuários personalizáveis
- Feed personalizado
- Receitas salvas
- Sistema de seguidores (próxima versão)
## Busca e Filtros Avançados
- Busca por texto (título, ingredientes, descrição, categorias)
- Filtro por dificuldade
- Ordenação por: popularidade, data, visualizações
- Paginação de resultados
- Estatísticas de receitas
## Autenticação e Segurança
- Sistema de registro e login
- Edição de perfil com foto
- Alteração de senha segura
- Proteção de rotas (@login_required)
- Upload seguro de imagens
- Validação server-side
- Hash Bcrypt para senhas
## Experiência do Usuário
- Design responsivo (mobile/desktop)
- Interface intuitiva e limpa
- Feedback visual imediato
- Navegação simplificada
- Botão de impressão com modal
- Badges coloridos por dificuldade
# Backend
- Flask 2.3.3 
    - Framework web minimalista e poderoso
- Flask-SQLAlchemy 3.0.5 
    - ORM para banco de dados
- Flask-Login 0.6.3 
    - Sistema de autenticação
- Flask-WTF 1.1.1 
    - Formulários web seguros
- Werkzeug 2.3.7 
    - Utilitários WSGI e segurança
- SQLAlchemy 2.0.23 
    - ORM avançado
# Frontend
- Bootstrap 5.1.3 
    - Framework CSS responsivo
- Jinja2 3.1.2 
    - Sistema de templates
- JavaScript Vanilla 
    - Interatividade sem frameworks
- Pillow 10.0.1 
    - Processamento de imagens
# Banco de Dados
- SQLite
    - Banco relacional embutido (desenvolvimento)
- Índices otimizados para performance
- Modelagem relacional com chaves estrangeiras