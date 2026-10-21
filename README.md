# Ditado

Ditado em português para Windows, com transcrição local usando o Whisper da OpenAI. Grave a partir de qualquer campo com **Ctrl+Alt+Espaço**, pare com o mesmo atalho e cole o texto com **Ctrl+V**.

O aplicativo fica perto do relógio, inicia junto com o Windows e permite revisar os textos em um painel. O pacote de instalação inclui Python, FFmpeg e os modelos; depois de baixá-lo, a instalação e o uso funcionam sem internet, conta OpenAI ou chave de API.

## Baixar

**[Baixar instalador offline — versão 2.0.0](https://github.com/vinnivii/Ditado/releases/download/v2.0.0/WhisperDitado-2.0.0.zip)** — aproximadamente 838 MB.

[Todas as versões](https://github.com/vinnivii/Ditado/releases) · [Arquivo SHA-256](https://github.com/vinnivii/Ditado/releases/download/v2.0.0/WhisperDitado-2.0.0.zip.sha256)

## Requisitos

- Windows 10 ou 11 de **64 bits**. A versão foi validada no Windows 10.
- Microfone conectado e com acesso permitido para aplicativos da área de trabalho.
- Aproximadamente **3 GB livres** para a instalação e seus arquivos temporários.
- A instalação é feita para o usuário atual, sem solicitar administrador.

## Instalação passo a passo

1. Baixe o arquivo **WhisperDitado-2.0.0.zip** pelo link acima.
2. Clique com o botão direito no ZIP e escolha **Extrair Tudo**.
3. Abra a pasta extraída que contém **Instalar.cmd**, **Instalar.ps1** e a pasta **aplicativo**. Mantenha esses itens juntos.
4. Dê dois cliques em **Instalar.cmd**. Aguarde a cópia, a conferência dos arquivos e a mensagem de conclusão; essa etapa pode levar alguns minutos.
5. Aguarde a notificação de que o Whisper está pronto. O ícone de microfone aparece perto do relógio, possivelmente dentro da seta de ícones ocultos.

O instalador cria o atalho **Whisper - Ditado de ocorrencias** na Área de Trabalho e no Menu Iniciar e configura a execução automática ao entrar no Windows.

### Instalação com um comando

Abra o PowerShell na pasta extraída que contém `Instalar.cmd` e execute:

```powershell
.\Instalar.cmd
```

O download em **Releases** contém o ambiente completo necessário ao instalador. Os arquivos de código deste repositório servem para consultar e desenvolver o projeto.

## Como usar

1. Aguarde o aviso de que o programa está pronto.
2. Clique no campo onde deseja colocar o texto.
3. Pressione **Ctrl+Alt+Espaço**. Após o sinal, comece a falar.
4. Pressione **Ctrl+Alt+Espaço** novamente para parar.
5. Aguarde os dois sinais e o aviso **Texto copiado**. Pressione **Ctrl+V** no campo desejado.

A transcrição acontece depois de encerrar a gravação. Cada ditado coloca **somente o trecho mais recente** na área de transferência, substituindo o conteúdo anterior. Cole o trecho antes de começar o próximo.

Para revisar o texto, trocar o microfone ou alterar o modelo, abra o atalho da Área de Trabalho ou use **Abrir painel** no menu do ícone perto do relógio. O painel reúne os ditados da sessão e permite editar, copiar tudo, salvar `.txt` e abrir arquivos de áudio.

**Fechar o painel mantém o atalho global ativo.** Para encerrar o aplicativo, clique com o botão direito no ícone perto do relógio e escolha **Sair**.

| Ícone | Estado |
| --- | --- |
| Verde | Pronto para gravar |
| Vermelho | Gravando o microfone |
| Amarelo | Preparando o modelo ou transcrevendo |

### Modelos disponíveis

- **Mais rápido — base:** modo inicial para reduzir o tempo de espera.
- **Mais precisão — small:** opção para priorizar o reconhecimento; pode levar mais tempo.

Dite em trechos de aproximadamente 30 a 60 segundos e revise nomes, números, datas, endereços e placas antes de registrar a ocorrência.

## Instalação em vários computadores

Copie a pasta extraída completa para um pendrive ou compartilhamento de rede. Execute o comando **no contexto do usuário que utilizará o aplicativo**.

Exemplo no PowerShell, a partir de um compartilhamento:

```powershell
& '\\servidor\programas\WhisperDitado-2.0.0\Instalar.cmd' -SemIniciar
```

Substitua o caminho pelo compartilhamento da sua organização. A opção `-SemIniciar` instala e deixa o programa configurado para iniciar no próximo logon.

| Opção | Efeito |
| --- | --- |
| `-SemIniciar` | Instala sem abrir o programa ao terminar |
| `-SemInicializacao` | Desativa a inicialização automática desta instalação |
| `-SemAtalhos` | Dispensa atalhos de Área de Trabalho e Menu Iniciar |
| `-Destino 'D:\Apps\WhisperDitado'` | Define outra pasta de instalação |

O caminho padrão é `%LOCALAPPDATA%\Programs\WhisperDitado`. O instalador retorna **0** em caso de sucesso e **1** em caso de falha. Ele verifica os hashes SHA-256 e as dependências antes de concluir.

Como a instalação é por usuário, executar o comando como `SYSTEM` instala para essa conta. Para ferramentas de gestão e scripts de logon, selecione o contexto do usuário. Consulte [IMPLANTACAO.txt](IMPLANTACAO.txt) para os detalhes.

### Atualizar

Saia pelo menu do ícone perto do relógio, extraia o novo pacote e execute `Instalar.cmd` novamente. As preferências são preservadas. O instalador avisa se a instalação de destino ainda estiver em uso.

## Solução de problemas

| Situação | O que fazer |
| --- | --- |
| Atalho sem resposta | Abra o aplicativo pelo atalho da Área de Trabalho e aguarde o modelo ficar pronto |
| Atalho ocupado | Feche o aplicativo em conflito ou use os botões do painel |
| Microfone sem áudio | Escolha outro dispositivo no painel e clique em **Atualizar** |
| Microfone bloqueado | Nas configurações de privacidade do Windows, permita acesso ao microfone para aplicativos da área de trabalho |
| Transcrição demorada | Use **Mais rápido — base** e dite trechos menores |
| Sem aviso sonoro | Acompanhe a notificação e o estado do ícone; confira **Avisos sonoros** no painel |

Preferências: `%LOCALAPPDATA%\WhisperDitado\config.json`.

Registro de erros: `%LOCALAPPDATA%\WhisperDitado\transcritor.log`.

## Processamento e arquivos

A transcrição é executada no computador. O aplicativo mantém o áudio do microfone em memória durante o processamento e não o salva em arquivo. Os textos da sessão ficam no painel; use **Salvar .txt** quando quiser guardá-los. O áudio de cada trecho tem limite de 10 minutos.

## Desinstalar

1. Encerre pelo menu **Sair** do ícone perto do relógio.
2. Remova a pasta `%LOCALAPPDATA%\Programs\WhisperDitado`, ou o destino personalizado escolhido.
3. Remova os atalhos **Whisper - Ditado de ocorrencias** da Área de Trabalho, do Menu Iniciar e da pasta Inicializar. Para abrir esta última, pressione `Win+R` e execute `shell:startup`.
4. Se desejar remover também as preferências e os logs, exclua `%LOCALAPPDATA%\WhisperDitado`.

## Organização do código

- `transcritor.py`: painel, gravação, transcrição, cópia automática e bandeja.
- `integracao_windows.py`: atalho global e controle de instância única.
- `Instalar.cmd` e `Instalar.ps1`: instalação por usuário e criação dos atalhos.
- `diagnostico.py`: verificação das dependências e dos modelos.
- `preparar_modelos.py`: download inicial dos modelos para desenvolvimento.
- `gerar_pacote.py`: montagem do pacote offline em Windows, a partir do ambiente de desenvolvimento preparado.
- `requirements-instalados.txt`: versões das dependências usadas nesta distribuição.

O ambiente de desenvolvimento usa Python 3.11, PyTorch para CPU e FFmpeg. O gerador do pacote utiliza o Python da sessão, as dependências do ambiente virtual, a pasta `modelos` e o FFmpeg instalado via Chocolatey. Os modelos, o runtime, os logs e os pacotes de distribuição ficam fora do histórico Git; o instalador completo está em **Releases**.

## Componentes de terceiros

Whisper e os modelos são da [OpenAI](https://github.com/openai/whisper). O aplicativo também utiliza Python, PyTorch, SoundDevice, Pystray, Pillow, FFmpeg e bibliotecas de execução do Visual C++.

Consulte [LICENCAS.txt](LICENCAS.txt) e mantenha os avisos e as licenças que acompanham o pacote ao redistribuí-lo.
