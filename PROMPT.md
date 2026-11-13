# Prompt mestre — site 3D em 9 passos (Claude Code + Blender)

Cole o bloco abaixo no Claude Code, numa pasta vazia. Troque só o que está entre `{chaves}`.
Se você não tiver alguma resposta, apague a linha: o Claude pergunta no passo certo.

```text
Vamos construir juntos um site 3D em 9 passos. Você conduz: em cada passo você me explica
em poucas linhas o que vai fazer e por quê, faz as perguntas daquele passo, executa, me
mostra o resultado e só avança quando eu disser "ok".

O QUE EU QUERO
- Negócio: {que empresa é e o que ela vende. Ex.: imobiliária, loja de tênis, clínica, restaurante}
- Objeto 3D: {o que vai aparecer em 3D. Ex.: planta de apartamento, tênis, cadeira, máquina, prédio}
- Objetivo da página: {o que o visitante deve fazer no final. Ex.: agendar visita, comprar, pedir orçamento}
- Marca: {caminho do arquivo com cores e fontes, ou "crie uma paleta simples comigo"}
- Referências: {caminhos de imagens do objeto e de sites que eu gosto, ou "vou mandar no passo 2"}

REGRAS DO TRABALHO
1. O objeto 3D é modelado por você, em código, no Blender rodando sem interface
   (blender -b -P script.py). Nada de baixar modelo pronto nem usar gerador de 3D.
2. Trabalhe em volta fechada: escreva o script, rode, renderize uma imagem, OLHE a imagem,
   liste o que está errado e corrija. No mínimo 3 voltas antes de me mostrar como pronto.
3. Use medida real. Se a referência tiver cotas ou escala (planta, desenho técnico, foto com
   objeto de tamanho conhecido), descubra quantos pixels valem 1 metro e modele em metros.
4. Um objeto herói só. Tudo na página gira em torno dele.
5. O site é um index.html + um scene.js, com Three.js por CDN (importmap). Sem build, sem
   framework, sem instalar dependência. Sirva com "python3 -m http.server" pra eu ver.
6. Texturas também são geradas por código (Python + PIL). Nada de imagem baixada.
7. Diga com clareza o que é medido e o que é chute seu. Se inventar um dado (andar, preço,
   orientação), avise e marque na página como ilustrativo.
8. Não invente depoimento, preço nem número de venda.

OS 9 PASSOS
1. OBJETO — confirme comigo o objeto herói e pra que serve a página. Diga se o objeto é bom
   pra 3D (precisa ser reconhecível de qualquer ângulo) e sugira alternativa se não for.
2. REFERÊNCIA — peça as imagens do objeto (quanto mais ângulos, melhor) e de 1 a 3 sites de
   referência. Leia tudo e me diga, numa tabela, o que você aproveita de cada referência.
   Descreva o objeto de volta pra mim pra eu conferir se você entendeu.
3. MARCA — transforme a marca em variáveis de CSS (cor de fundo, cor de texto, 1 cor de ação,
   fontes, raio, sombra). Pergunte se o objeto fica realista ou na paleta da marca.
4. MODELAGEM — escreva o script do Blender. Uma função "caixa" que recebe coordenadas da
   referência e alturas em metros resolve 90% do trabalho. Materiais com nome. Renderize 3
   vistas (de cima, 3/4, detalhe) e compare com a referência lado a lado.
5. EXPORTAR — exporte em .glb com texturas embutidas em JPEG. Meta: abaixo de 5 MB.
   Procedural do Blender não exporta: textura tem que ser imagem ligada na cor base.
6. PALCO — monte a cena no Three.js: luz principal quente com sombra, luz de preenchimento,
   uma luz na cor da marca, tone mapping ACES, vidro como material físico transparente.
   Tire um print, confira exposição e sombra, corrija.
7. COREOGRAFIA — defina uma POSE de câmera por seção da página (alvo, azimute, elevação,
   distância, deslocamento lateral). O scroll só informa "estou X% entre a seção A e a B" e o
   código mistura as duas poses. A câmera segura a pose no meio da seção e viaja na passagem.
   A câmera tem inércia. O objeto fica do lado oposto do texto.
8. PÁGINA — escreva as seções por cima do 3D: topo com título e botão, uma seção por parte
   do objeto (com 2 números reais cada), e um fechamento com a chamada pra ação.
9. POLIMENTO — teste em tela de celular (390x844): o objeto sobe, o texto fica embaixo.
   Reduza resolução e sombra no celular. Adicione tela de carregamento. Só publique quando
   eu pedir.

MÓDULOS OPCIONAIS (me pergunte no passo 1 se algum faz sentido)
- CONTEXTO: modelar também o "em volta" do objeto (o prédio de um apartamento, a loja de um
  produto) e fazer a câmera voar de fora pra dentro, com o exterior ficando transparente.
- SOL: simulador de luz natural com a posição real do sol (latitude da cidade, estação do
  ano e hora), pra ver sombra e incidência.
- VARIAÇÕES: botões que trocam cor, material ou acabamento do objeto.

COMO ME RESPONDER
- Curto. O que você decidiu, o que ficou pronto, o que trava.
- Sempre que gerar imagem, me mostre a imagem.
- No fim de cada passo: "Pronto pra começar o passo N. Me dá o ok."

Comece agora pelo passo 1.
```

## Os pedidos que eu fiz durante a live (resumo fiel)

O site do apartamento não saiu de um prompt só. Saiu desta sequência de mensagens curtas:

1. "Quero fazer um site 3D com o Fable 5.2 apenas, sem gerador de 3D. Monta uma metodologia em passos e vai me fazendo as perguntas e explicando, como se a gente estivesse em live."
2. "Não tem como você usar o Blender pra fazer o objeto 3D?"
3. "Vamos fazer uma planta de apartamento para um site de imobiliária, pro cara conseguir entrar e ver essa planta em 3D." (+ imagem da planta)
4. "Maquete aberta." (+ duas pastas de sites de referência + uma imagem do Pinterest)
5. "Usa o branding da Core." Depois: "maquete realista."
6. "Tenta achar esse prédio da planta." (+ link do blog da construtora)
7. "Consegui essas duas fotos do prédio. Na hero quero o prédio inteiro, como um take de drone entrando na unidade. E quero ver onde o sol nasce e se põe, e as estações do ano."
8. "Ok, pode começar o passo N" — entre cada passo.

O prompt mestre acima junta tudo isso num pedido só, pra você não depender de lembrar a ordem.
