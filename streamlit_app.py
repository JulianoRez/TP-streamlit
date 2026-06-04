import math
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --- Configuracoes da Pagina ---
st.set_page_config(
    page_title="ICD - Acidentes BH",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS Customizado ---
st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; color: #1E3A8A; font-weight: 700; margin-bottom: 0;}
    .sub-header {font-size: 1.2rem; color: #64748B; margin-bottom: 2rem;}
    .highlight {color: #2563EB; font-weight: bold;}
    .metric-card {background-color: #F8FAFC; padding: 1rem; border-radius: 8px; border: 1px solid #E2E8F0;}
    </style>
""", unsafe_allow_html=True)

COLOR_PALETTE = px.colors.qualitative.Prism

# --- Funcoes Auxiliares de Formatacao ---
def format_int(value): return f"{int(round(value)):,}".replace(",", ".")
def format_pct(value, digits=2): return f"{value * 100:.{digits}f}%".replace(".", ",")
def format_float(value, digits=2): return f"{value:.{digits}f}".replace(".", ",")

# --- Paginas ---
def page_intro():
    st.markdown('<p class="main-header">Acidentes de Transito em Belo Horizonte</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Dashboard Analitico - Introducao a Ciencia de Dados</p>', unsafe_allow_html=True)
    
    st.write("""
        Bem-vindo ao dashboard interativo do nosso estudo sobre acidentes de transito.
        Este projeto integra diferentes bases publicas para extrair padroes estatisticos reais sobre 
        letalidade, sazonalidade e fatores de risco no transito da capital mineira.
    """)
    
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Registros Processados", "1.040.217", delta="2012 a 2025", delta_color="off")
    with col2: st.metric("Vitimas Analisadas", "182.739")
    with col3: st.metric("Condicoes da Via", "179.492")
    with col4: st.metric("Veiculos Envolvidos", "6.5M+")
    
    st.divider()
    
    st.markdown("### Perguntas de Pesquisa")
    colA, colB = st.columns(2)
    with colA:
        st.info("P1: Qual perfil demografico apresenta maior proporcao de vitimas graves ou fatais?")
        st.success("P2: Como os acidentes se distribuem no tempo e e possivel prever volumes futuros?")
    with colB:
        st.warning("P3: O tipo ou porte do veiculo influencia a gravidade das vitimas?")
        st.error("P4: Problemas de infraestrutura influenciam a gravidade dos acidentes?")

def page_tratamento():
    st.title("Tratamento das Bases")
    st.markdown("Esta secao detalha o fluxo de limpeza e padronizacao dos dados utilizados para cada uma das perguntas de pesquisa, conforme os scripts do projeto.")

    tab1, tab2, tab3, tab4 = st.tabs(["P1: Vitimas", "P2: Ocorrencias Temporais", "P3: Veiculos", "P4: Condicoes da Via"])

    with tab1:
        st.subheader("Base de Vitimas (Pergunta 1)")
        st.markdown("""
        **Limpeza e padronizacao dos dados:**
        - Foi aplicado um *Join* (intersecao) entre as bases anuais de vitimas e de ocorrencias usando a chave `numero_ocorrencia_associado`.
        - Aplicou-se o filtro do municipio de Belo Horizonte (`nome_municipio == 'BELO HORIZONTE'`).
        - Padronizacao dos nomes das colunas para minusculas, sem acentos e em *snake_case*.
        - Normalizacao dos textos em maiusculas, sem acentos e sem espacos duplicados.
        - Remocao de registros duplicados utilizando o atributo `numero_ocorrencia_env` (pois uma mesma ocorrencia pode possuir mais de uma vitima).
        - Remocao de vitimas que nao apresentam a chave de ocorrencia.
        - O resultado foi salvo como `vitimas_limpo.csv`.
        
        **Dicionario de Dados Principais:**
        - `envolvimento_descricao`: Descricao do tipo de envolvimento da vitima.
        - `condicao_fisica_descricao`: Condicao fisica registrada (FATAL, GRAVES OU INCONSCIENTE, LEVES, SEM LESOES, etc).
        - `valor_idade_aparente`: Idade aparente da vitima.
        - `codigo_sexo` e `cor_pele_descricao`: Genero e raca informados.
        """)

    with tab2:
        st.subheader("Base de Registros (Pergunta 2)")
        st.markdown("""
        **Limpeza e padronizacao dos dados:**
        - A base utilizada foi a de registros de ocorrencias, pois contem as variaveis temporais necessarias (hora, dia, mes e ano).
        - Arquivos anuais carregados e unidos. Filtro para Belo Horizonte.
        - Padronizacao dos textos e colunas.
        - Remocao de registros sem identificador e eliminacao de duplicatas pela chave `numero_ocorrencia_associado`.
        - Conversao de `data_fato` e `horario_fato` para formatos padronizados, extraindo-se `dia_fato` e `hora_fato`.
        - Remocao final de nulos gerados na conversao de data/hora.
        - Arquivo gerado: `registros_limpo.csv`.
        
        **Dicionario de Dados Principais:**
        - `data_fato`: data padronizada do acidente no formato AAAA-MM-DD.
        - `horario_fato`: horario completo do acidente.
        - `hora_fato`: hora inteira do acidente, usada para analisar os picos horarios.
        - `dia_da_semana`: dia da semana em que o acidente ocorreu.
        """)

    with tab3:
        st.subheader("Base de Veiculos (Pergunta 3)")
        st.markdown("""
        **Limpeza e padronizacao dos dados:**
        - **Veiculos:** Agrupamento de tipos de veiculos e correcoes ortograficas (ex: "Caminhonete (CHASSI)" e "Caminhonete (Monobloco)" consolidadas em "CAMINHONETE").
        - **Juncao:** Base de veiculos unida a base de vitimas. 
        - **Agrupamentos amplos:** Veiculos consolidados em "PORTE LEVE", "BICICLETA", "MOTO", "MICROONIBUS", "ONIBUS" e "CAMINHAO".
        - Condicoes das vitimas agrupadas em "FATAL", "GRAVE", "LEVE", "SEM LESAO" e "OUTROS".
        - Exclusao de veiculos raros (Quadriciclo, Trator, etc) que possuiam numero muito pequeno de acidentes.
        """)

    with tab4:
        st.subheader("Base de Condicoes da Via (Pergunta 4)")
        st.markdown("""
        **Limpeza e padronizacao dos dados:**
        - Foi notado que a representacao de valores nulos nas tabelas era informada textualmente como `"NAO INFORMADO"`.
        - Esses termos foram substituidos por `NaN` e as linhas removidas usando `dropna()`.
        - Cruzamento do *dataframe* limpo de condicoes com a tabela limpa de ocorrencias (registros) para associar as ocorrencias apenas a Belo Horizonte.
        - Arquivo utilizado para analise do cruzamento de parametros de gravidade e estado da infraestrutura local (ex: via simples, luminosidade, etc).
        """)

def page_pergunta_1():
    st.title("Pergunta 1: Perfil Demografico")
    
    tab1, tab2, tab3 = st.tabs(["Exploracao", "Testes e IC", "Conclusoes"])
    
    with tab1:
        st.write("Visualizacao da proporcao de vitimas graves ou fatais por perfil, conforme apurado na limpeza do grupo (removidos ignorados e nulos).")
        
        sexo = pd.DataFrame({"Sexo": ["Homens", "Mulheres"], "Taxa": [0.0904, 0.0702]})
        cor = pd.DataFrame({"Cor/Raca": ["Negra", "Preto", "Parda", "Branca"], "Taxa": [0.0972, 0.0860, 0.0855, 0.0797]})
        faixa = pd.DataFrame({"Faixa Etaria": ["80+", "70-79", "60-69", "18-29"], "Taxa": [0.1608, 0.1287, 0.1148, 0.0761]})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            fig1 = px.bar(sexo, x="Sexo", y="Taxa", text=sexo["Taxa"].apply(lambda x: format_pct(x, 2)), 
                          title="Gravidade por Sexo", template="plotly_white", color_discrete_sequence=[COLOR_PALETTE[0]])
            fig1.update_layout(yaxis_tickformat=".0%")
            st.plotly_chart(fig1, use_container_width=True)
            
        with col2:
            fig2 = px.bar(cor, x="Cor/Raca", y="Taxa", text=cor["Taxa"].apply(lambda x: format_pct(x, 2)), 
                          title="Gravidade por Cor/Raca", template="plotly_white", color_discrete_sequence=[COLOR_PALETTE[1]])
            fig2.update_layout(yaxis_tickformat=".0%")
            st.plotly_chart(fig2, use_container_width=True)
            
        with col3:
            fig3 = px.bar(faixa, x="Faixa Etaria", y="Taxa", text=faixa["Taxa"].apply(lambda x: format_pct(x, 2)), 
                          title="Gravidade por Faixa Etaria", template="plotly_white", color_discrete_sequence=[COLOR_PALETTE[2]])
            fig3.update_layout(yaxis_tickformat=".0%")
            st.plotly_chart(fig3, use_container_width=True)

    with tab2:
        st.subheader("Teste de Hipotese: Homens Jovens (18-25) e Pardos")
        st.markdown("""
        **H0:** A proporcao de casos graves ou fatais nesse grupo e igual ou menor que nos demais perfis.  
        **H1:** A proporcao e maior.
        """)
        
        colA, colB, colC = st.columns(3)
        colA.metric("Homens pardos 18-25 (Graves/Total)", "1.127 / 13.815")
        colB.metric("Taxa Observada (Grupo)", "8,16%")
        colC.metric("Taxa Demais Perfis", "8,57%")
        
        st.info("**Estatistica Z:** -1.5960 | **p-valor (unilateral):** 0.9448")
        st.warning("A estatistica z resultou em -1,5960 e o p-valor em 0,9448, bem acima do limiar de 5%. A hipotese nula nao e rejeitada. Logo a proporcao observada no grupo de interesse ficou abaixo da dos demais perfis, contrariando a hipotese.")

    with tab3:
        st.success("""
        **Conclusao:**
        
        Jovens concentram mais ocorrencias, mas nao os desfechos mais graves. E como observado esse padrao aparece nas faixas etarias mais altas, o que faz sentido: seres humanos mais jovens concentram mais ocorrencias, porem o padrao de letalidade aparece nas faixas etarias mais altas. E isso tambem faz sentido, pessoas mais velhas toleram menos o trauma e se recuperam com mais dificuldade.
        
        A distincao importa porque volume e gravidade nao andam juntos. Um grupo pode dominar os registros por estar mais exposto, enquanto outro, menos frequente, converte a mesma ocorrencia em consequencia mais seria. Ignorar essa diferenca distorce tanto a leitura dos dados quanto as prioridades de intervencao.
        """)

def page_pergunta_2():
    st.title("Pergunta 2: Distribuicao Temporal")
    
    hora_dados = pd.DataFrame({
        "Hora": [f"{i:02d}h" for i in range(24)],
        "Ocorrencias": [10884, 7225, 5312, 4420, 4382, 6508, 21447, 52467, 57856, 57074, 57848, 60571, 62267, 64704, 68664, 70678, 73835, 78870, 81402, 68092, 48086, 33595, 26263, 17767]
    })
    
    semana_dados = pd.DataFrame({
        "Dia da Semana": ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"],
        "Media Diaria": [220.9, 215.9, 219.0, 216.0, 241.5, 183.8, 126.7]
    })
    
    mes_dados = pd.DataFrame({
        "Mes": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"],
        "Media Diaria": [169.9, 204.5, 205.3, 195.0, 199.5, 200.6, 197.2, 211.7, 214.1, 213.3, 217.5, 212.8]
    })
    
    ano_dados = pd.DataFrame({
        "Ano": list(range(2012, 2026)),
        "Ocorrencias": [77077, 77096, 76933, 72944, 69263, 73158, 72497, 79843, 58257, 61828, 69112, 79047, 84548, 88614]
    })
    
    tab1, tab2, tab3 = st.tabs(["Analise Exploratoria", "Testes e IC", "Conclusoes"])
    
    with tab1:
        st.write("Agrupamos os acidentes por hora, dia da semana e mes. Usamos **medias diarias** para evitar vieses de calendario.")
        
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(hora_dados, x="Hora", y="Ocorrencias", title="Volume por Hora (Pico em Vermelho)", template="plotly_white")
            fig1.add_vrect(x0=16.5, x1=19.5, fillcolor="red", opacity=0.15, line_width=0)
            st.plotly_chart(fig1, use_container_width=True)
            
            fig3 = px.bar(mes_dados, x="Mes", y="Media Diaria", title="Media Diaria por Mes", template="plotly_white", color_discrete_sequence=[COLOR_PALETTE[2]])
            st.plotly_chart(fig3, use_container_width=True)
            
        with col2:
            fig2 = px.bar(semana_dados, x="Dia da Semana", y="Media Diaria", title="Media Diaria por Dia da Semana", template="plotly_white", color_discrete_sequence=[COLOR_PALETTE[1]])
            st.plotly_chart(fig2, use_container_width=True)
            
            fig4 = px.line(ano_dados, x="Ano", y="Ocorrencias", markers=True, title="Serie Anual de Acidentes", template="plotly_white", color_discrete_sequence=[COLOR_PALETTE[3]])
            st.plotly_chart(fig4, use_container_width=True)

    with tab2:
        st.subheader("Validacao Estatistica das Hipoteses")
        colA, colB = st.columns(2)
        with colA:
            st.info("""
            **1. Horario de pico de 17h a 19h**
            * **H0:** Se os acidentes fossem distribuidos uniformemente ao longo do dia, a faixa de 17h a 19h teria 12,5% dos acidentes (p0 = 0,125).
            * **H1:** A proporcao de acidentes entre 17h e 19h e significativamente maior que 12,5%.
            * **Resultado:** A proporcao observada foi de **21,95%**, com um Intervalo de Confianca (IC) de 95% entre **[21,87%, 22,03%]**.
            * **Conclusao:** Como o limite inferior do IC e superior a 12,5% e o p-valor resultante e extremamente proximo de zero (p < 0,001), rejeitamos a hipotese nula. Conclui-se que ha uma concentracao estatisticamente relevante de acidentes no horario de saida do trabalho.
            """)
        with colB:
            st.warning("""
            **2. Madrugada de fim de semana**
            * **H0:** A proporcao de acidentes entre 00h e 05h e igual em fins de semana e dias uteis.
            * **H1:** A proporcao de acidentes entre 00h e 05h e maior nos fins de semana.
            * **Resultado:** Nos fins de semana, a proporcao foi **8,78%**; nos dias uteis, foi **2,31%**. A diferenca observada foi de **6,47** pontos percentuais, com um IC de 95% para a diferenca entre **[6,35%, 6,59%]**.
            * **Conclusao:** Como o intervalo nao inclui o valor zero e o p-valor e significativamente menor que alpha, rejeitamos a hipotese nula. Concluimos que a madrugada de fim de semana apresenta uma vulnerabilidade temporal distinta em relacao aos dias uteis.
            """)

    with tab3:
        st.success("""
        **Resultados da analise exploratoria:**
        
        Foram analisadas um pouco mais de um milhao de ocorrencias entre 2012 e 2025. Nao houve ausencia nas principais variaveis temporais usadas na analise.
        
        O pico isolado ocorre as 18h, com 81.402 ocorrencias. A faixa de 17h a 19h concentra 228.364 acidentes, o equivalente a 21,95% de todos os registros. Se os acidentes fossem uniformes ao longo das 24 horas, essa faixa de 3 horas deveria concentrar apenas 12,50% dos casos.
        
        A sexta-feira apresenta a maior media diaria, com aproximadamente 241,5 acidentes por dia. O domingo apresenta a menor media diaria.
        
        A madrugada de fim de semana tambem se destacou. Sabados e domingos apresentaram 8,78% dos acidentes nesse periodo, enquanto os dias uteis apresentaram 2,31%.
        
        Na analise mensal, o menor nivel ocorreu em janeiro, e o maior em novembro. Isso sugere maior volume de acidentes no segundo semestre.
        
        Na serie anual, e interessante notar uma queda de 2019 para 2020, provavelmente associada a reducao de circulacao durante a pandemia de COVID-19.
        """)

def page_pergunta_3():
    st.title("Pergunta 3: Tipo de Veiculo vs Severidade")
    
    tab1, tab2, tab3 = st.tabs(["Analise Geral", "Testes Especificos (A/B e Bootstrap)", "Conclusoes"])
    with tab1:
        st.write("Analise da relacao entre configuracao veicular (porte pesado e motos) e a presenca de vitimas graves ou fatais.")
        st.info("O agrupamento identificou veiculos de grande massa (Onibus, Micro-onibus e Caminhoes) versus demais veiculos, e testou a hipotese do impacto ser pior com veiculos pesados e com motocicletas.")
        
        grupos = pd.DataFrame({
            "Envolvimento": ["Pesados (Geral)", "Pesados (Pedestres)", "Motos (Condutores/Passageiros)"],
            "Diferenca Observada Media": ["Positiva (+)", "Positiva (++)", "Negativa (-)"]
        })
        st.table(grupos)

    with tab2:
        st.subheader("Testes de Hipotese (Diferenca nas Taxas Medias de Gravidade)")

        colA, colB, colC = st.columns(3)
        with colA:
            st.info("""
            **1. Veiculos Pesados (Pedestres)**  
            * **H0:** Acidentes que envolvem veiculos pesados e nao pesados tendem a, em media, possuir iguais proporcoes de vitimas pedestres em estado grave.  
            * **HA:** Acidentes que envolvem veiculos pesados tendem a, em media, possuir maiores proporcoes de vitimas pedestres em estado grave do que os demais tipos de veiculo.  
            * **Resultado:** Com esse teste, nossa hipotese nula pode ser rejeitada, pois ela nao pertence ao IC mostrado. A diferenca media observada e positiva, o que nos permite tomar a hipotese alternativa como verdadeira.
            """)
        with colB:
            st.warning("""
            **2. Motos (Condutores e Passageiros)**  
            * **H0:** Acidentes que envolvem motos e nao motos tendem a, em media, possuir iguais proporcoes de vitimas condutoras ou passageiras em estado grave.  
            * **HA:** Acidentes que envolvem motos tendem a, em media, possuir maiores proporcoes de vitimas condutoras ou passageiras em estado grave do que os demais tipos de veiculo.  
            * **Resultado:** A hipotese nula e rejeitada, pois ela nao pertence ao IC. Todavia, a diferenca media observada e negativa, o que nao esta de acordo com a hipotese alternativa, pois, para tanto, a media devia ser positiva. Acidentes exclusivos de motos e suas vitimas possuem, em media, menores taxas em estado grave, quando comparados a veiculos nao motos.
            """)
        with colC:
            st.success("""
            **Uso do Bootstrap**  
            Para a comparacao da diferenca entre proporcoes de vitimas pesadas e nao pesadas, foi construida uma distribuicao Bootstrap de 5.000 subamostras.  
            Os limites de 2,5% e 97,5% da distribuicao do Bootstrap excluíram o zero (Hipotese Nula), confirmando estatisticamente as observacoes com um alto rigor de amostragem.
            """)

    with tab3:
        st.success("""
        **Conclusoes:**
        
        Com os resultados, foi possivel concluir que os acidentes envolvendo veiculos pesados possuem maiores taxas medias de vitimas em estado grave se comparado a veiculos nao pesados. Essa diferenca fica ainda maior quando as vitimas sao pedestres. Ainda, vale ressaltar que nao foi possivel concluir que, em acidentes envolvendo condutores ou passageiros, as motos tendem a possuir maiores proporcoes medias deles em estado grave se comparado a veiculos que nao sao motos.

        O resultado para veiculos pesados condisse com nossa suposicao, uma vez que, fisicamente, um corpo acelerado com maior massa produz maior forca sobre um objeto (nesse caso, sendo o objeto a vitima ou um veiculo que a contem). Nao somente, o resultado de que, analisando as vitimas pedestres, a diferenca entre veiculos pesados e nao pesados aumenta faz sentido, pois, estando a vitima desprotegida, como toda a forca vai direto para ela e nao e dissipada em nenhum outro obstaculo, espera-se que ocorram mais casos de vitimas em estado grave.

        Por outro lado, o resultado para motos nao condisse com o esperado. A suposicao era a de que, pelo fato de motos possuirem maior velocidade media e maior exposicao do usuario, a taxa media de condutores e passageiros envolvidos em acidentes com motos seria maior quando comparado com os veiculos que nao sao motos. Todavia, o resultado nao foi o desejado, e nao foi possivel concluir a hipotese alternativa.

        Parece, entao, que o fator porte do veiculo possui maior associacao com a maior proporcao media de vitimas em estado grave.
        """)

def page_pergunta_4():
    st.title("Pergunta 4: Infraestrutura da Via")
    
    tab1, tab2, tab3 = st.tabs(["Analise Exploratoria", "Testes de Hipotese (A/B)", "Conclusoes"])
    with tab1:
        st.write("A analise focou em tres vertentes da infraestrutura em Belo Horizonte: Capacidade da Via, Luminosidade e Sinalizacao.")
        
        pav_df = pd.DataFrame({"Tipo de Pavimento": ["Asfalto", "Nao Informado", "Calcamento", "Concreto", "Outros", "Terra"], "Porcentagem": [95.59, 1.97, 1.17, 0.66, 0.53, 0.04]}).sort_values("Porcentagem")
        via_df = pd.DataFrame({"Tipo de Via": ["Pista Simples", "Pista Dupla", "Pista Multipla", "Nao Informado"], "Porcentagem": [52.87, 26.28, 20.20, 0.66]}).sort_values("Porcentagem")
        sin_df = pd.DataFrame({"Sinalizacao": ["Boa", "Nao Ha", "Em Mas Condicoes", "Nao Informado", "Irregular"], "Porcentagem": [74.63, 16.83, 3.56, 3.20, 1.78]}).sort_values("Porcentagem")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            fig1 = px.bar(pav_df, y="Tipo de Pavimento", x="Porcentagem", orientation='h', title="Pavimento (Asfalto absoluto)", template="plotly_white")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.bar(via_df, y="Tipo de Via", x="Porcentagem", orientation='h', title="Tipo da Pista", template="plotly_white")
            st.plotly_chart(fig2, use_container_width=True)
        with col3:
            fig3 = px.bar(sin_df, y="Sinalizacao", x="Porcentagem", orientation='h', title="Sinalizacao", template="plotly_white")
            st.plotly_chart(fig3, use_container_width=True)
            
        st.markdown("""
        1. A maioria esmagadora dos acidentes acontecem no asfalto, podendo levar a insights sobre a falsa sensacao de seguranca.
        2. Outra maioria exorbitante e de acidentes em pistas simples, o que nos leva a possivelmente entender como essas pistas levam a mais colisoes frontais em ultrapassagens.
        3. A sinalizacao e predominantemente boa, compondo mais de 60% dos casos de acidentes. Isso indica que a falta de sinalizacao nao e uma das causas primarias para os acidentes.
        """)

    with tab2:
        st.subheader("Testes Estatisticos de Associacao")
        
        colA, colB, colC = st.columns(3)
        with colA:
            st.info("""
            **1. Tipo da Via (Simples vs Nao Simples)**  
            * **H0:** A pavimentacao e tipo da via nao tem influencia na gravidade.  
            * **Resultado:** Ao comparar a diferenca entre os grupos “via simples” e “via nao simples” na curva normal, tornou-se claro uma proporcao de 5.225% com intervalo de confianca de 95%.  
            * **Conclusao:** Esse intervalo exclui a hipotese nula, logo a rejeitamos. A pavimentacao da via foi descartada devido a discrepancia enorme entre os tamanhos dos grupos.
            """)
        with colB:
            st.warning("""
            **2. Iluminacao (Boa vs Nao Ha)**  
            * **H0:** A iluminacao nao tem influencia na gravidade.  
            * **Resultado:** Ao comparar a diferenca, tornou-se claro uma proporcao de 21.7%, com intervalo de confianca de 95%.  
            * **Conclusao:** Esse valor esta muito acima da marca de 5%, e, portanto, nao foi possivel rejeitar a hipotese nula.
            """)
        with colC:
            st.error("""
            **3. Sinalizacao (Ha vs Nao Ha)**  
            * **H0:** A sinalizacao nao tem influencia na gravidade.  
            * **Resultado:** Ao comparar a diferenca entre os grupos, percebe-se que essa diferenca girava em torno de 0, ou seja, inclui a hipotese nula.  
            * **Conclusao:** Devido a isso nao foi possivel rejeitar a hipotese nula de que a sinalizacao isoladamente afeta a gravidade do acidente em BH.
            """)

    with tab3:
        st.success("""
        **Conclusoes:**
        Os resultados determinam que o tipo de via e a variavel de maior impacto na gravidade do acidente, e a unica que permitiu rejeitar a hipotese nula. As condicoes das vias simples tornam acidentes graves mais propensos. Quanto as variaveis de iluminacao e sinalizacao, nao foi observada evidencia forte o suficiente para rejeitar a hipotese nula. Isso sugere que, em Belo Horizonte, acidentes tendem a independer da iluminacao e sinalizacao, tendendo as duas a no geral serem boas.
        """)

def page_conclusao():
    st.title("Conclusoes e Modelos da Pesquisa")
    
    tab1, tab2 = st.tabs(["O que aprendemos", "Proposta de Machine Learning"])
    
    with tab1:
        st.markdown("""
        ### Sintese dos Achados
        - **P1 Demografia:** Jovens concentram mais ocorrencias, mas nao os desfechos mais graves. O padrao de letalidade aparece nas faixas etarias mais altas. Um grupo pode dominar os registros por estar mais exposto, enquanto outro converte a mesma ocorrencia em consequencia mais seria.
        - **P2 Temporalidade:** O volume absoluto foca na saida do trabalho (18h) em dias uteis, mas a madrugada do final de semana carrega uma diferenca significativa no risco proporcional de letalidade em acidentes.
        - **P3 Veiculos:** A inercia domina o fator de gravidade: acidentes envolvendo veiculos pesados possuem maiores taxas medias de vitimas em estado grave se comparado a veiculos nao pesados. Essa diferenca fica ainda maior quando as vitimas sao pedestres.
        - **P4 Infraestrutura:** Os resultados determinam que o tipo de via (simples vs dupla/multipla) e a variavel de maior impacto na gravidade do acidente, e a unica que permitiu rejeitar a hipotese nula de infraestrutura.
        """)
        
    with tab2:
        st.markdown("""
        ### Discussao: O que poderiamos treinar usando Aprendizado de Maquina?
        O monitor apontou que temos a liberdade de aplicar classificacoes ou regressoes que facam sentido para o contexto do trabalho. Observando as nossas conclusoes estatisticas, sugerimos duas abordagens fortes de Inteligencia Artificial:

        #### 1. Classificador Logistico: O "Alerta" para o Samu
        Como os Testes A/B e o Bootstrap comprovaram que Tipo de Veiculo (Inercia) e Idade da Vitima (Fragilidade) sao chaves estatisticas para desfechos severos, a primeira recomendacao e usar um algoritmo de Classificacao Binaria (como Regressao Logistica ou Arvore de Decisao).
        - **Target:** `Grave_ou_Fatal` (1 ou 0).
        - **Features:** Hora, Tipo de Veiculo (Pesado = 1), Idade da Vitima.
        - **Uso real:** O centro de despacho de ambulancias recebe a notificacao da batida e o modelo cospe: "Probabilidade de vitima grave: 82%".

        #### 2. Regressao Linear Multipla: Sazonalidade Pos-Pandemia
        Vimos na Pergunta 2 que as series anuais e medias mensais flutuam muito. Mas sera que da pra prever os numeros brutos do mes que vem?
        - **Target:** `Quantidade de Acidentes`.
        - **Features:** Uma variavel `Tempo` sequencial para capturar crescimento da frota, e *Dummies* de `Mes` (Jan a Dez) para que o modelo entenda que Novembro e sazonalmente pior que Janeiro.
        - **Metrica:** Avaliaria o erro absoluto medio (MAE). Serviria para o planejamento de ferias da Policia de Transito ou campanhas publicitarias preventivas.
        """)

# --- Roteamento ---
PAGES = {
    "Introducao": page_intro,
    "Tratamento das Bases": page_tratamento,
    "P1: Perfil Demografico": page_pergunta_1,
    "P2: Tempo e Sazonalidade": page_pergunta_2,
    "P3: Veiculos Envolvidos": page_pergunta_3,
    "P4: Infraestrutura": page_pergunta_4,
    "Conclusoes Finais": page_conclusao
}

st.sidebar.title("Navegacao")
selection = st.sidebar.radio("Ir para:", list(PAGES.keys()))
st.sidebar.divider()
st.sidebar.caption("TP de ICD - UFMG | Dashboards com Streamlit e Plotly")

PAGES[selection]()
