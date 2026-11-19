# SoloSync 🌱

Um sistema web desenvolvido em Django para o gerenciamento de propriedades rurais, controle de talhões, acompanhamento de safras (plantios) e registros de atividades rotineiras no campo.

## Funcionalidades

- **Gestão de Talhões (Áreas):** Cadastre os espaços de terra da sua propriedade informando área em m², tipo de solo (Arenoso, Argiloso, Misto, Siltoso) e coordenadas geográficas.
- **Controle de Plantios (Safras):** Acompanhe o que está plantado em cada talhão, desde o preparo do solo até a colheita, com cálculo automático do progresso do ciclo, estimativa da data de colheita e dias restantes.
- **Registro de Manejos:** Controle aplicações de defensivos, adubações, podas, capinas e colheita, registrando os produtos, insumos e dosagens utilizados.
- **Controle de Irrigação:** Acompanhe a duração e o volume de água aplicado em cada plantio.
- **Monitoramento de Ocorrências:** Registre eventos no campo como pragas, doenças, deficiências nutricionais e danos climáticos, além da ação tomada para reverter a situação.

## Tecnologias Utilizadas

- [Python](https://www.python.org/)
- [Django 6.1](https://www.djangoproject.com/) (Framework Web)
- SQLite3 (Banco de Dados embutido)
- `python-dotenv` (Variáveis de ambiente)
- `Pillow` (Processamento de imagens)

## Pré-requisitos

Para rodar este projeto, você precisará ter instalado:
- [Python 3](https://www.python.org/downloads/)
- [Git](https://git-scm.com/) (opcional, para clonar o repositório)

## Como Executar o Projeto Localmente

Siga o passo a passo abaixo para configurar o ambiente e rodar o projeto na sua máquina:

```bash
# 1. Acesse a pasta do projeto
$ cd gestao_agricola

# 2. Crie um ambiente virtual (Recomendado)
$ python -m venv venv

# 3. Ative o ambiente virtual
# No Windows:
$ venv\Scripts\activate
# No Linux/Mac:
$ source venv/bin/activate

# 4. Instale as dependências do projeto
$ pip install -r requirements.txt

# 5. Crie o arquivo de variáveis de ambiente
# Crie um arquivo `.env` na raiz do projeto com as suas configurações (como SECRET_KEY).
# Você pode usar um `.env.example` como base, se disponível.

# 6. Execute as migrações do banco de dados
$ python manage.py migrate

# 7. Crie um superusuário para ter acesso ao painel de administração
$ python manage.py createsuperuser

# 8. Colete os arquivos estáticos
$ python manage.py collectstatic --noinput

# 9. Inicie o servidor de desenvolvimento
$ python manage.py runserver
```

> O servidor iniciará localmente. Acesse em seu navegador: `http://127.0.0.1:8000/` ou `http://localhost:8000/`.

## Estrutura de Dados Principal

* **Talhão:** Áreas cultiváveis de um usuário específico.
* **Plantio:** Cultivo ocorrendo dentro de um Talhão, com informações sobre o ciclo, datas e progresso.
* **Manejo:** Tratos culturais aplicados em um Plantio específico.
* **Irrigação:** Controle de regas por Plantio.
* **Ocorrência:** Registro de incidentes e ações corretivas em um Plantio.

## JavaScript no SoloSync

O projeto utiliza JavaScript moderno (ES6+) em `static/js/solosync.js` integrado ao Django:

- validação de formulários no navegador, sem substituir o `ModelForm` e a validação do servidor;
- confirmação interativa antes da exclusão;
- filtros dinâmicos de propriedades, talhões e plantios;
- máscara da UF, formatação de números decimais e feedback visual;
- atualização dinâmica dos campos agronômicos no cadastro de plantio;
- melhoria de usabilidade em formulários de propriedade, talhão, plantio e irrigação.

Operações de banco, autenticação, relacionamentos e permissões continuam processadas pelo Django. Não há endpoints JavaScript que contornem o CSRF ou a autenticação.

## Configuração de ambiente

Copie o modelo e gere uma chave segura:

```bash
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

No Windows, use `Copy-Item .env.example .env`. Configure no `.env`:

```env
DEBUG=True
SECRET_KEY=sua-chave-gerada
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1
SQLITE_PATH=db.sqlite3
```

O arquivo `.env` nunca deve ser versionado. Em produção, use `DEBUG=False`, uma `SECRET_KEY` exclusiva, hosts explícitos, HTTPS e uma origem CSRF `https://...`.


## Verificação

```bash
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py check --deploy
```

## Implantação no Google Cloud

Consulte `DEPLOYMENT.md` para a preparação completa de Ubuntu, Python, SQLite persistente, Gunicorn, Nginx, HTTPS, Certbot, backups e inicialização automática no Google Compute Engine.
