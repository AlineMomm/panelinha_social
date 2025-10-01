# PROJETO PANELINHA SOCIAL
Rede Social de Receitas 
Atividade para a Matéria Desenvolvimento de Sistemas Web


# Estou usando:
- Python
- Flask
- Flask-WTF
- WTForms
- Flask-SQLAlchemy
- Flask-Login

# Tela inicial / Feed
- Cards de receitas com:
    - Foto principal da receita.
    - Nome da receita
    - Nome do autor
    - Curtir, comentar e salvar
- Opção de ordenar feed (mais recentes, mais populares, recomendadas pelo perfil do usuário).

# Tela de postagem de receita
- Upload de foto da galeria ou tirar foto na hora.
- Campos para:
    - Título da receita.
    - Descrição curta.
    - Ingredientes cada item listado.
    - Passos do preparo (com numeração automática).
    - Botão para publicar e opção de salvar rascunho.
    - marcar categorias (ex: "vegano", "massa").

# Tela de pesquisa e filtros
- Barra de busca (por nome da receita ou nome do autor).
- Filtros:
    - Por ingredientes disponíveis
    - Por categoria (sobremesa, almoço, vegano…).
    - Por popularidade (mais curtidas, mais comentadas).

# Tela de perfil do usuário
- Foto de perfil + bio.
- Contador de receitas publicadas, curtidas recebidas, seguidores/seguindo.
- Aba “Receitas publicadas” + aba “Favoritos”.
- Opção de editar perfil.
- Timeline pessoal (receitas que a pessoa postou).

# Para fazer se der tempo
- Modo escuro (dark mode)
- Receitas colaborativas → um usuário posta a base e outros podem sugerir variações.
- Gamificação → conquistas (“10 receitas postadas”, “Primeira receita com mais de 100 curtidas”).
- Modo “lista de compras” → ao selecionar uma receita, o app gera a lista de ingredientes para comprar no mercado.
