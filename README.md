# Gestão Agrícola 

Um sistema web desenvolvido em Django para o gerenciamento de propriedades rurais, controle de talhões, acompanhamento de safras (plantios) e registros de atividades rotineiras no campo.

## Funcionalidades

- **Gestão de Talhões (Áreas):** Cadastre os espaços de terra da sua propriedade informando área em m², tipo de solo (Arenoso, Argiloso, Misto, Siltoso) e coordenadas geográficas.
- **Controle de Plantios (Safras):** Acompanhe o que está plantado em cada talhão, desde o preparo do solo até a colheita, com cálculo automático do progresso do ciclo, estimativa da data de colheita e dias restantes.
- **Registro de Manejos:** Controle aplicações de defensivos, adubações, podas, capinas e colheita, registrando os produtos, insumos e dosagens utilizados.
- **Controle de Irrigação:** Acompanhe a duração e o volume de água aplicado em cada plantio.
- **Monitoramento de Ocorrências:** Registre eventos no campo como pragas, doenças, deficiências nutricionais e danos climáticos, além da ação tomada para reverter a situação.

## Tecnologias Utilizadas

- [Python](https://www.python.org/)
- [Django](https://www.djangoproject.com/) (Framework Web)
- SQLite3 (Banco de Dados embutido)
- `python-dotenv` (Variáveis de ambiente)
- `Pillow` (Processamento de imagens)

## Pré-requisitos

Para rodar este projeto, você precisará ter instalado:
- [Python 3](https://www.python.org/downloads/)
- [Git](https://git-scm.com/) (opcional, para clonar)

## Como Executar o Projeto Localmente

```bash
# Acesse a pasta do projeto
$ cd gestao_agricola

# Crie e ative um ambiente virtual (Recomendado)
$ python -m venv venv
$ venv\Scripts\activate

# Instale as dependências do projeto
$ pip install -r requirements.txt

# Execute as migrações do banco de dados
$ python manage.py migrate

# Crie um superusuário para ter acesso ao painel de administração
$ python manage.py createsuperuser

# Inicie o servidor de desenvolvimento
$ python manage.py runserver
```

> O servidor iniciará localmente. Acesse em seu navegador: `http://127.0.0.1:8000/` ou `http://localhost:8000/`.

## Estrutura de Dados Principal

* **Talhão:** Áreas cultiváveis de um usuário específico.
* **Plantio:** Cultivo ocorrendo dentro de um Talhão, com informações sobre o ciclo, datas e progresso.
* **Manejo:** Tratos culturais aplicados em um Plantio específico.
* **Irrigação:** Controle de regas por Plantio.
* **Ocorrência:** Registro de incidentes e ações corretivas em um Plantio.
