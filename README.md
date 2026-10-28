# InfoClima - Alerta de queimadas

Projeto de extensão que consulta focos de incêndio detectados por satélites da NASA na região configurada, gera um mapa com imagem de satélite e envia um boletim para um grupo do WhatsApp usando a Green-API.

## O que o programa faz

Ao executar `boletim.py`, o sistema:

1. Consulta as fontes VIIRS SNPP, VIIRS NOAA-20 e MODIS do NASA FIRMS para as últimas 48 horas.
2. Remove coordenadas duplicadas e gera `mapa_queimadas.png`, destacando os focos e pontos de referência locais.
3. Cria um link do Google Maps para o foco mais próximo de Novo Remanso.
4. Envia o mapa e o texto do boletim para o grupo configurado na Green-API.

O mapa também pode ser gerado quando não há focos encontrados. A execução envia o boletim mesmo nesse caso.

## Requisitos

- Python 3.10 ou superior
- Uma chave de API do [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/api/).
- Uma instância configurada na [Green-API](https://green-api.com/) para envio de mensagens pelo WhatsApp.
- Acesso à internet para consultar os dados e carregar o mapa-base de satélite.

## Instalação

No PowerShell, na pasta do projeto:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação do ambiente virtual, consulte a política de execução configurada no Windows ou execute os comandos usando `venv\Scripts\python.exe` sem ativá-lo.

## Configuração

Crie um arquivo `.env` na raiz do projeto com as credenciais e configurações:

```dotenv
NASA_MAP_KEY=sua_chave_nasa_firms
WA_INSTANCE_ID=id_da_instancia_green_api
WA_API_TOKEN=token_da_instancia_green_api
WA_GROUP_ID=id_do_grupo_no_whatsapp
BBOX=-59.35,-3.25,-58.95,-2.85
```

`NASA_MAP_KEY` é usada na consulta ao NASA FIRMS. `WA_INSTANCE_ID`, `WA_API_TOKEN` e `WA_GROUP_ID` configuram o envio pela Green-API. `BBOX` é opcional; se omitida, o programa usa a área padrão acima.

`BBOX` define os limites geográficos na ordem `oeste,sul,leste,norte` (longitude e latitude, em graus). Ajuste os valores para a região de interesse. As coordenadas de Novo Remanso usadas para escolher o foco mais próximo estão definidas diretamente em `boletim.py`.

Não compartilhe nem versione o arquivo `.env`: ele contém credenciais e já está listado no `.gitignore`.

## Execução

Com o ambiente virtual ativado e o `.env` configurado:

```powershell
python boletim.py
```

O mapa é salvo como `mapa_queimadas.png` na pasta do projeto e também é enviado com o boletim ao grupo configurado. A imagem gerada é ignorada pelo Git.

## Dependências

As bibliotecas Python usadas pelo projeto estão listadas em [`requirements.txt`](requirements.txt). O mapa-base é obtido do serviço de imagens da Esri por meio do Contextily; sua disponibilidade depende do acesso à internet.

## Observações importantes

- Este boletim é informativo e não substitui alertas oficiais, orientações das autoridades ou serviços de emergência.
- Os dados podem estar atrasados, indisponíveis ou sujeitos a limitações de detecção. Uma consulta sem resultados não confirma a ausência de incêndios.
- O foco indicado como mais próximo é calculado por distância aproximada entre coordenadas, não por distância rodoviária.
- O código atual gera um boletim e tenta enviá-lo a cada execução, inclusive se a consulta não retornar focos.
