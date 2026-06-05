import math
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --- Configurações da Página ---
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

# --- Funções Auxiliares de Formatação ---
def format_int(value): return f"{int(round(value)):,}".replace(",", ".")
def format_pct(value, digits=2): return f"{value * 100:.{digits}f}%".replace(".", ",")
def format_float(value, digits=2): return f"{value:.{digits}f}".replace(".", ",")

# --- Páginas ---
def page_intro():
    st.markdown('<p class="main-header">Acidentes de Trânsito em Belo Horizonte</p>', unsafe_allow_html=True)
    
    
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Registros Processados", "1.040.217", delta="2012 a 2025", delta_color="off")
    with col2: st.metric("Vítimas Analisadas", "182.739")
    with col3: st.metric("Condições da Via", "179.492")
    with col4: st.metric("Veículos Envolvidos", "6.5M+")
    
    st.divider()
    
    st.markdown("### Perguntas de Pesquisa")
    colA, colB = st.columns(2)
    with colA:
        st.info("P1: Qual perfil demográfico apresenta maior proporção de vítimas graves ou fatais?")
        st.success("P2: Como os acidentes se distribuem no tempo e é possível prever volumes futuros?")
    with colB:
        st.warning("P3: O tipo ou porte do veículo influencia a gravidade das vítimas?")
        st.error("P4: Problemas de infraestrutura influenciam a gravidade dos acidentes?")

def page_tratamento():
    st.title("Tratamento das Bases")

    tab1, tab2, tab3, tab4 = st.tabs(["P1: Vítimas", "P2: Ocorrências Temporais", "P3: Veículos", "P4: Condições da Via"])

    with tab1:
        st.subheader("Base de Vítimas (Pergunta 1)")
        st.markdown("""
        **Limpeza e padronização dos dados:**
        - Foi aplicado um *Join* (interseção) entre as bases anuais de vítimas e de ocorrências usando a chave `numero_ocorrencia_associado`.
        - Aplicou-se o filtro do município de Belo Horizonte (`nome_municipio == 'BELO HORIZONTE'`).
        - Padronização dos nomes das colunas para minúsculas, sem acentos e em *snake_case*.
        - Normalização dos textos em maiúsculas, sem acentos e sem espaços duplicados.
        - Remoção de registros duplicados utilizando o atributo `numero_ocorrencia_env` (pois uma mesma ocorrência pode possuir mais de uma vítima).
        - Remoção de vítimas que não apresentam a chave de ocorrência.
        - O resultado foi salvo como `vitimas_limpo.csv`.
        
        **Dicionário de Dados Principais:**
        - `envolvimento_descricao`: Descrição do tipo de envolvimento da vítima.
        - `condicao_fisica_descricao`: Condição física registrada (FATAL, GRAVES OU INCONSCIENTE, LEVES, SEM LESOES, etc).
        - `valor_idade_aparente`: Idade aparente da vítima.
        - `codigo_sexo` e `cor_pele_descricao`: Gênero e raça informados.
        """)

    with tab2:
        st.subheader("Base de Registros (Pergunta 2)")
        st.markdown("""
        **Limpeza e padronização dos dados:**
        - A base utilizada foi a de registros de ocorrências, pois contém as variáveis temporais necessárias (hora, dia, mês e ano).
        - Arquivos anuais carregados e unidos. Filtro para Belo Horizonte.
        - Padronização dos textos e colunas.
        - Remoção de registros sem identificador e eliminação de duplicatas pela chave `numero_ocorrencia_associado`.
        - Conversão de `data_fato` e `horario_fato` para formatos padronizados, extraindo-se `dia_fato` e `hora_fato`.
        - Remoção final de nulos gerados na conversão de data/hora.
        - Arquivo gerado: `registros_limpo.csv`.
        
        **Dicionário de Dados Principais:**
        - `data_fato`: data padronizada do acidente no formato AAAA-MM-DD.
        - `horario_fato`: horário completo do acidente.
        - `hora_fato`: hora inteira do acidente, usada para analisar os picos horários.
        - `dia_da_semana`: dia da semana em que o acidente ocorreu.
        """)

    with tab3:
        st.subheader("Base de Veículos (Pergunta 3)")
        st.markdown("""
        **Limpeza e padronização dos dados:**
        - **Veículos:** Agrupamento de tipos de veículos e correções ortográficas (ex: "Caminhonete (CHASSI)" e "Caminhonete (Monobloco)" consolidadas em "CAMINHONETE").
        - **Junção:** Base de veículos unida à base de vítimas. 
        - **Agrupamentos amplos:** Veículos consolidados em "PORTE LEVE", "BICICLETA", "MOTO", "MICROONIBUS", "ONIBUS" e "CAMINHAO".
        - Condições das vítimas agrupadas em "FATAL", "GRAVE", "LEVE", "SEM LESAO" e "OUTROS".
        - Exclusão de veículos raros (Quadriciclo, Trator, etc) que possuíam número muito pequeno de acidentes.
        """)

    with tab4:
        st.subheader("Base de Condições da Via (Pergunta 4)")
        st.markdown("""
        **Limpeza e padronização dos dados:**
        - Foi notado que a representação de valores nulos nas tabelas era informada textualmente como `"NAO INFORMADO"`.
        - Esses termos foram substituídos por `NaN` e as linhas removidas usando `dropna()`.
        - Cruzamento do *dataframe* limpo de condições com a tabela limpa de ocorrências (registros) para associar as ocorrências apenas a Belo Horizonte.
        - Arquivo utilizado para análise do cruzamento de parâmetros de gravidade e estado da infraestrutura local (ex: via simples, luminosidade, etc).
        """)

def page_pergunta_1():
    st.title("Pergunta 1: Perfil Demográfico")
    
    tab1, tab2, tab3 = st.tabs(["Exploração", "Testes e IC", "Conclusões"])
        
    r_sexo = pd.DataFrame({
        'codigo_sexo': ['M', 'F'],
        'proporcao': [9.04, 7.02]
    })
    
    r_cor = pd.DataFrame({
        'cor_pele_descricao': ['BRANCA', 'PARDA', 'PRETO', 'NEGRA', 'AMARELA', 'ALBINA', 'INDIGENA'],
        'proporcao': [7.97, 8.55, 8.60, 9.72, 12.30, 13.39, 17.65]
    })
    
    r_faixa = pd.DataFrame({
        'faixa_etaria': ['18 A 29 ANOS', '30 A 39 ANOS', '0 A 11 ANOS', '40 A 49 ANOS', '50 A 59 ANOS', '12 A 17 ANOS', '60 A 69 ANOS', '70 A 79 ANOS', '80 ANOS OU MAIS'],
        'proporcao': [7.61, 8.40, 8.40, 8.68, 9.64, 11.22, 11.48, 12.87, 16.08]
    })

    top10 = pd.DataFrame({
        'perfil': [
            'M | PARDA | 12 A 17 ANOS', 
            'F | PRETO | 30 A 39 ANOS', 
            'M | PARDA | 60 A 69 ANOS',
            'M | BRANCA | 70 A 79 ANOS', 
            'F | BRANCA | 80 ANOS OU MAIS', 
            'F | PARDA | 80 ANOS OU MAIS',
            'M | NEGRA | 60 A 69 ANOS', 
            'M | PARDA | 80 ANOS OU MAIS', 
            'M | NEGRA | 12 A 17 ANOS',
            'M | BRANCA | 80 ANOS OU MAIS'
        ],
        'proporcao': [12.64, 13.53, 13.85, 14.74, 15.24, 15.83, 15.92, 16.54, 17.61, 18.49]
    })
    with tab1:
        st.subheader("Proporção de vítimas graves ou fatais por perfil demográfico")

        col1, col2, col3 = st.columns(3)

        with col1:
            fig_sexo = px.bar(r_sexo, x='codigo_sexo', y='proporcao', 
                              title="Por sexo", text='proporcao', 
                              labels={'codigo_sexo': '', 'proporcao': 'Proporção (%)'},
                              color_discrete_sequence=["#2F6B8A"])
            fig_sexo.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig_sexo.update_layout(yaxis_range=[0, r_sexo['proporcao'].max() * 1.3])
            st.plotly_chart(fig_sexo, use_container_width=True)

        with col2:
            fig_cor = px.bar(r_cor, y='cor_pele_descricao', x='proporcao', orientation='h',
                             title="Por cor/raça", text='proporcao',
                             labels={'cor_pele_descricao': '', 'proporcao': 'Proporção (%)'},
                             color_discrete_sequence=["#6C8F5A"])
            fig_cor.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig_cor.update_layout(xaxis_range=[0, r_cor['proporcao'].max() * 1.3])
            st.plotly_chart(fig_cor, use_container_width=True)

        with col3:
            fig_faixa = px.bar(r_faixa, y='faixa_etaria', x='proporcao', orientation='h',
                               title="Por faixa etária", text='proporcao',
                               labels={'faixa_etaria': '', 'proporcao': 'Proporção (%)'},
                               color_discrete_sequence=["#A66A45"])
            fig_faixa.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig_faixa.update_layout(xaxis_range=[0, r_faixa['proporcao'].max() * 1.3])
            st.plotly_chart(fig_faixa, use_container_width=True)

        st.divider()
        
        st.subheader("Perfis demográficos com maior proporção")
        fig_top10 = px.bar(top10, y='perfil', x='proporcao', orientation='h',
                           text='proporcao', labels={'perfil': '', 'proporcao': 'Proporção (%)'},
                           color_discrete_sequence=["#4C7A93"])
        fig_top10.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig_top10.update_layout(xaxis_range=[0, top10['proporcao'].max() * 1.2], height=450)
        st.plotly_chart(fig_top10, use_container_width=True)

    with tab2:
        st.subheader("Teste de Hipótese: Homens Jovens (18-25) e Pardos")
        st.markdown("""
        **H0:** A proporção de casos graves ou fatais nesse grupo é igual ou menor que nos demais perfis.  
        **H1:** A proporção é maior.
        """)
        
        colA, colB, colC = st.columns(3)
        colA.metric("Homens pardos 18-25 (Graves/Total)", "1.127 / 13.815")
        colB.metric("Taxa Observada (Grupo)", "8,16%")
        colC.metric("Taxa Demais Perfis", "8,57%")
        
        st.info("**Estatística Z:** -1.5960 | **p-valor (unilateral):** 0.9448")
        st.warning("A estatística z resultou em -1,5960 e o p-valor em 0,9448, bem acima do limiar de 5%. A hipótese nula não é rejeitada. Logo a proporção observada no grupo de interesse ficou abaixo da dos demais perfis, contrariando a hipótese.")

    with tab3:
        st.success("""
        **Conclusão:**
        
        Jovens concentram mais ocorrências, mas não os desfechos mais graves. E como observado esse padrão aparece nas faixas etárias mais altas, o que faz sentido: seres humanos mais jovens concentram mais ocorrências, porém o padrão de letalidade aparece nas faixas etárias mais altas. E isso também faz sentido, pessoas mais velhas toleram menos o trauma e se recuperam com mais dificuldade.
        
        A distinção importa porque volume e gravidade não andam juntos. Um grupo pode dominar os registros por estar mais exposto, enquanto outro, menos frequente, converte a mesma ocorrência em consequência mais séria. Ignorar essa diferença distorce tanto a leitura dos dados quanto as prioridades de intervenção.
        """)

def page_pergunta_2():
    st.title("Pergunta 2: Distribuição Temporal")
    
    hora_dados = pd.DataFrame({
        "Hora": [f"{i:02d}h" for i in range(24)],
        "Ocorrências": [10884, 7225, 5312, 4420, 4382, 6508, 21447, 52467, 57856, 57074, 57848, 60571, 62267, 64704, 68664, 70678, 73835, 78870, 81402, 68092, 48086, 33595, 26263, 17767]
    })
    
    semana_dados = pd.DataFrame({
        "Dia da Semana": ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"],
        "Média Diária": [220.9, 215.9, 219.0, 216.0, 241.5, 183.8, 126.7]
    })
    
    mes_dados = pd.DataFrame({
        "Mês": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"],
        "Média Diária": [169.9, 204.5, 205.3, 195.0, 199.5, 200.6, 197.2, 211.7, 214.1, 213.3, 217.5, 212.8]
    })
    
    ano_dados = pd.DataFrame({
        "Ano": list(range(2012, 2026)),
        "Ocorrências": [77077, 77096, 76933, 72944, 69263, 73158, 72497, 79843, 58257, 61828, 69112, 79047, 84548, 88614]
    })
    
    tab1, tab2, tab3 = st.tabs(["Análise Exploratória", "Testes e IC", "Conclusões"])
    
    with tab1:
        
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(hora_dados, x="Hora", y="Ocorrências", title="Volume por Hora (Pico em Vermelho)", template="plotly_white")
            fig1.add_vrect(x0=16.5, x1=19.5, fillcolor="red", opacity=0.15, line_width=0)
            st.plotly_chart(fig1, use_container_width=True)
            
            fig3 = px.bar(mes_dados, x="Mês", y="Média Diária", title="Média Diária por Mês", template="plotly_white", color_discrete_sequence=[COLOR_PALETTE[2]])
            st.plotly_chart(fig3, use_container_width=True)
            
        with col2:
            fig2 = px.bar(semana_dados, x="Dia da Semana", y="Média Diária", title="Média Diária por Dia da Semana", template="plotly_white", color_discrete_sequence=[COLOR_PALETTE[1]])
            st.plotly_chart(fig2, use_container_width=True)
            
            fig4 = px.line(ano_dados, x="Ano", y="Ocorrências", markers=True, title="Série Anual de Acidentes", template="plotly_white", color_discrete_sequence=[COLOR_PALETTE[3]])
            st.plotly_chart(fig4, use_container_width=True)

    with tab2:
        st.subheader("Validação Estatística das Hipóteses")
        colA, colB = st.columns(2)
        with colA:
            st.info("""
            **1. Horário de pico de 17h a 19h**
            * **H0:** Se os acidentes fossem distribuídos uniformemente ao longo do dia, a faixa de 17h a 19h teria 12,5% dos acidentes (p0 = 0,125).
            * **H1:** A proporção de acidentes entre 17h e 19h é significativamente maior que 12,5%.
            * **Resultado:** A proporção observada foi de **21,95%**, com um Intervalo de Confiança (IC) de 95% entre **[21,87%, 22,03%]**.
            * **Conclusão:** Como o limite inferior do IC é superior a 12,5% e o p-valor resultante é extremamente próximo de zero (p < 0,001), rejeitamos a hipótese nula. Conclui-se que há uma concentração estatisticamente relevante de acidentes no horário de saída do trabalho.
            """)
        with colB:
            st.warning("""
            **2. Madrugada de fim de semana**
            * **H0:** A proporção de acidentes entre 00h e 05h é igual em fins de semana e dias úteis.
            * **H1:** A proporção de acidentes entre 00h e 05h é maior nos fins de semana.
            * **Resultado:** Nos fins de semana, a proporção foi **8,78%**; nos dias úteis, foi **2,31%**. A diferença observada foi de **6,47** pontos percentuais, com um IC de 95% para a diferença entre **[6,35%, 6,59%]**.
            * **Conclusão:** Como o intervalo não inclui o valor zero e o p-valor é significativamente menor que alpha, rejeitamos a hipótese nula. Concluímos que a madrugada de fim de semana apresenta uma vulnerabilidade temporal distinta em relação aos dias úteis.
            """)

    with tab3:
        st.success("""
        **Resultados da análise exploratória:**
        
        Foram analisadas um pouco mais de um milhão de ocorrências entre 2012 e 2025. Não houve ausência nas principais variáveis temporais usadas na análise.
        
        O pico isolado ocorre às 18h, com 81.402 ocorrências. A faixa de 17h a 19h concentra 228.364 acidentes, o equivalente a 21,95% de todos os registros. Se os acidentes fossem uniformes ao longo das 24 horas, essa faixa de 3 horas deveria concentrar apenas 12,50% dos casos.
        
        A sexta-feira apresenta a maior média diária, com aproximadamente 241,5 acidentes por dia. O domingo apresenta a menor média diária.
        
        A madrugada de fim de semana também se destacou. Sábados e domingos apresentaram 8,78% dos acidentes nesse período, enquanto os dias úteis apresentaram 2,31%.
        
        Na análise mensal, o menor nível ocorreu em janeiro, e o maior em novembro. Isso sugere maior volume de acidentes no segundo semestre.
        
        Na série anual, é interessante notar uma queda de 2019 para 2020, provavelmente associada à redução de circulação durante a pandemia de COVID-19.
        """)

import streamlit as st
import pandas as pd
import plotly.express as px

def page_pergunta_3():
    st.title("Pergunta 3: Tipo de Veículo vs Severidade")
    
    tab1, tab2, tab3 = st.tabs(["Análise Geral", "Testes Específicos (A/B e Bootstrap)", "Conclusões"])
    
    with tab1:
        st.subheader("Proporção de Lesões por Tipo de Veículo")
        
        # ==========================================
        # 1. DADOS HARDCODED (Valores extraídos das imagens)
        # ==========================================
        
        # Tabela 1: Geral
        dados_geral = pd.DataFrame({
            "Tipo de Veículo": ["BICICLETA", "CAMINHAO", "MICROONIBUS", "MOTO", "ONIBUS", "PORTE LEVE"],
            "SEM LESAO": [0.060, 0.065, 0.070, 0.060, 0.070, 0.075],
            "LEVE":      [0.760, 0.720, 0.750, 0.780, 0.760, 0.780],
            "GRAVE":     [0.070, 0.100, 0.080, 0.070, 0.065, 0.050],
            "FATAL":     [0.015, 0.035, 0.015, 0.010, 0.015, 0.010],
            "OUTROS":    [0.090, 0.070, 0.075, 0.085, 0.085, 0.085]
        })

        # Tabela 2: Pedestres
        dados_pedestres = pd.DataFrame({
            "Tipo de Veículo": ["BICICLETA", "CAMINHAO", "MICROONIBUS", "MOTO", "ONIBUS", "PORTE LEVE"],
            "SEM LESAO": [0.040, 0.040, 0.055, 0.050, 0.055, 0.060],
            "LEVE":      [0.730, 0.580, 0.700, 0.700, 0.640, 0.710],
            "GRAVE":     [0.120, 0.200, 0.150, 0.135, 0.170, 0.105],
            "FATAL":     [0.010, 0.085, 0.020, 0.020, 0.050, 0.025],
            "OUTROS":    [0.110, 0.090, 0.070, 0.090, 0.080, 0.095]
        })

        # Tabela 3: Condutores e Passageiros
        dados_condutores = pd.DataFrame({
            "Tipo de Veículo": ["BICICLETA", "CAMINHAO", "MICROONIBUS", "MOTO", "ONIBUS", "PORTE LEVE"],
            "SEM LESAO": [0.060, 0.060, 0.070, 0.060, 0.065, 0.070],
            "LEVE":      [0.760, 0.740, 0.760, 0.780, 0.780, 0.800],
            "GRAVE":     [0.070, 0.100, 0.075, 0.070, 0.050, 0.045],
            "FATAL":     [0.015, 0.030, 0.015, 0.010, 0.015, 0.010],
            "OUTROS":    [0.090, 0.070, 0.075, 0.085, 0.085, 0.085]
        })

        # Cores idênticas à sua legenda original
        mapa_cores = {
            "SEM LESAO": "green", 
            "LEVE": "yellow", 
            "GRAVE": "orange", 
            "FATAL": "red", 
            "OUTROS": "gray"
        }

        # Função auxiliar para gerar o gráfico sem repetir código
        def criar_grafico(df, titulo):
            # Transforma a tabela larga no formato ideal para o Plotly
            df_melt = df.melt(id_vars="Tipo de Veículo", var_name="Condição Física", value_name="Proporção")
            
            fig = px.bar(
                df_melt, 
                x="Tipo de Veículo", 
                y="Proporção", 
                color="Condição Física",
                barmode="group", # Isso faz as barras ficarem lado a lado
                title=titulo,
                color_discrete_map=mapa_cores
            )
            # Trava o eixo Y para ficar padronizado igual às suas imagens (até 0.8 / 80%)
            fig.update_layout(yaxis_range=[0, 0.85], xaxis_title="") 
            return fig

        # ==========================================
        # 2. EXIBIÇÃO NO STREAMLIT
        # ==========================================
        
        # Cria um botão de seleção para o usuário navegar entre as 3 visões sem poluir a tela
        visao = st.radio(
            "Selecione o grupo analisado:", 
            ["Geral", "Apenas Pedestres", "Condutores e Passageiros"],
            horizontal=True
        )

        if visao == "Geral":
            st.plotly_chart(criar_grafico(dados_geral, "Proporção de Lesões por Tipo de Veículo"), use_container_width=True)
        
        elif visao == "Apenas Pedestres":
            st.plotly_chart(criar_grafico(dados_pedestres, "Proporção de Lesões por Tipo de Veículo para Pedestres"), use_container_width=True)
            
        else:
            st.plotly_chart(criar_grafico(dados_condutores, "Proporção de Lesões por Tipo de Veículo para Condutores e Passageiros"), use_container_width=True)

    # O RESTANTE DO SEU CÓDIGO PERMANECE INTOCADO (Abaixo)
    with tab2:
        st.subheader("Testes de Hipótese")
        colA, colB, colC = st.columns(3)
        with colA:
            st.info("""
            **1. Veículos Pesados (Pedestres)** * **H0:** Acidentes que envolvem veículos pesados e não pesados tendem a, em média, possuir iguais proporções de vítimas pedestres em estado grave.  
            * **HA:** Acidentes que envolvem veículos pesados tendem a, em média, possuir maiores proporções de vítimas pedestres em estado grave do que os demais tipos de veículo.  
            * **Resultado:** Com esse teste, nossa hipótese nula pode ser rejeitada, pois ela não pertence ao IC mostrado. A diferença média observada é positiva, o que nos permite tomar a hipótese alternativa como verdadeira.
            """)
            st.image("images/Figure_1.png", use_container_width=True)
        with colB:
            st.warning("""
            **2. Motos (Condutores e Passageiros)** * **H0:** Acidentes que envolvem motos e não motos tendem a, em média, possuir iguais proporções de vítimas condutoras ou passageiras em estado grave.  
            * **HA:** Acidentes que envolvem motos tendem a, em média, possuir maiores proporções de vítimas condutoras ou passageiras em estado grave do que os demais tipos de veículo.  
            * **Resultado:** A hipótese nula é rejeitada, pois ela não pertence ao IC. Todavia, a diferença média observada é negativa, o que não está de acordo com a hipótese alternativa, pois, para tanto, a média devia ser positiva. Acidentes exclusivos de motos e suas vítimas possuem, em média, menores taxas em estado grave, quando comparados a veículos não motos.
            """)
            st.image("images/Figure_3.png", use_container_width=True)
        with colC:
            st.success("""
            **Uso do Bootstrap** Para a comparação da diferença entre proporções de vítimas pesadas e não pesadas, foi construída uma distribuição Bootstrap de 5.000 subamostras.  
            Os limites de 2,5% e 97,5% da distribuição do Bootstrap excluíram o zero (Hipótese Nula), confirmando estatisticamente as observações com um alto rigor de amostragem.
            """)
            st.image("images/teste.png", use_container_width=True)

    with tab3:
        st.success("""
        **Conclusões:**
        
        Com os resultados, foi possível concluir que os acidentes envolvendo veículos pesados possuem maiores taxas médias de vítimas em estado grave se comparado a veículos não pesados. Essa diferença fica ainda maior quando as vítimas são pedestres. Ainda, vale ressaltar que não foi possível concluir que, em acidentes envolvendo condutores ou passageiros, as motos tendem a possuir maiores proporções médias deles em estado grave se comparado a veículos que não são motos.

        O resultado para veículos pesados condisse com nossa suposição, uma vez que, fisicamente, um corpo acelerado com maior massa produz maior força sobre um objeto (nesse caso, sendo o objeto a vítima ou um veículo que a contém). Não somente, o resultado de que, analisando as vítimas pedestres, a diferença entre veículos pesados e não pesados aumenta faz sentido, pois, estando a vítima desprotegida, como toda a força vai direto para ela e não é dissipada em nenhum outro obstáculo, espera-se que ocorram mais casos de vítimas em estado grave.

        Por outro lado, o resultado para motos não condisse com o esperado. A suposição era a de que, pelo fato de motos possuírem maior velocidade média e maior exposição do usuário, a taxa média de condutores e passageiros envolvidos em acidentes com motos seria maior quando comparado com os veículos que não são motos. Todavia, o resultado não foi o desejado, e não foi possível concluir a hipótese alternativa.

        Parece, então, que o fator porte do veículo possui maior associação com a maior proporção média de vítimas em estado grave.
        """)

def page_pergunta_4():
    st.title("Pergunta 4: Infraestrutura da Via")
    
    tab1, tab2, tab3 = st.tabs(["Análise Exploratória", "Testes de Hipótese (A/B)", "Conclusões"])
    
    with tab1:
        st.write("A análise focou em três vertentes da infraestrutura em Belo Horizonte: Tipo de Via, Tipo de Pavimento e a relação entre Sinalização e Luminosidade.")
        
        # ==========================================
        # 1. DADOS HARDCODED (Valores aproximados)
        # ==========================================
        
        # 1.1 Dados: Tipo de Via
        dados_via = pd.DataFrame({
            "Tipo de Via": ["PISTA SIMPLES", "PISTA DUPLA", "PISTA MULTIPLA", "NAO INFORMADO"],
            "Quantidade": [1020000, 350000, 100000, 10000]
        }).sort_values("Quantidade", ascending=True)

        # 1.2 Dados: Tipo de Pavimento
        dados_pavimento = pd.DataFrame({
            "Tipo de Pavimento": ["ASFALTO", "CALCAMENTO", "CONCRETO", "OUTROS (NO HISTORICO)", "TERRA", "CASCALHO (MINERAL)"],
            "Quantidade": [168000, 2500, 1000, 800, 100, 50]
        }).sort_values("Quantidade", ascending=True)

        # 1.3 Dados: Sinalização por Condição de Luz
        dados_sinalizacao = pd.DataFrame({
            "Luminosidade": ["AMANHECER", "DIA", "ENTARDECER", "NAO INFORMADO", "NOITE SEM ILUMINACAO", "NOITE/ILUMINACAO ARTIFICIAL"],
            "BOA": [63.0, 58.0, 55.0, 6.0, 62.0, 56.0],
            "EM MAS CONDICOES": [4.0, 4.0, 4.0, 1.0, 4.0, 4.0],
            "IRREGULAR": [3.0, 2.0, 2.0, 0.0, 3.0, 2.0],
            "NAO HA": [28.0, 34.0, 36.0, 5.0, 29.0, 36.0],
            "NAO INFORMADO": [2.0, 2.0, 3.0, 88.0, 2.0, 2.0]
        })
        df_sinal_melt = dados_sinalizacao.melt(
            id_vars="Luminosidade", 
            var_name="Condição Sinalização", 
            value_name="Porcentagem"
        )

        # ==========================================
        # 2. CRIAÇÃO DOS GRÁFICOS (PLOTLY)
        # ==========================================
        
        fig_via = px.bar(
            dados_via, y="Tipo de Via", x="Quantidade", orientation='h',
            title="Acidentes por Tipo de Via",
            color="Tipo de Via",
            color_discrete_sequence=["#F4A261", "#D65C70", "#7B3275", "#3A1B61"]
        )
        fig_via.update_layout(xaxis_title="Quantidade de Acidentes", yaxis_title="", showlegend=False, height=500)

        fig_pavimento = px.bar(
            dados_pavimento, y="Tipo de Pavimento", x="Quantidade", orientation='h',
            title="Distribuição de Acidentes por Tipo de Pavimento",
            color_discrete_sequence=["#43326B"]
        )
        fig_pavimento.update_layout(xaxis_title="Quantidade de Ocorrências", yaxis_title="", height=500)

        cores_sinal = {"BOA": "#4C72B0", "EM MAS CONDICOES": "#DD8452", "IRREGULAR": "#55A868", "NAO HA": "#C44E52", "NAO INFORMADO": "#8172B3"}
        fig_sinal = px.bar(
            df_sinal_melt, x="Luminosidade", y="Porcentagem", color="Condição Sinalização",
            title="Qualidade da Sinalização por Condição de Luz",
            barmode="stack",
            color_discrete_map=cores_sinal
        )
        fig_sinal.update_layout(yaxis_title="Porcentagem (%)", xaxis_title="Condição de Luminosidade", legend_title="Condição da Sinalização", height=600)
        
        # ==========================================
        # 3. INTERFACE DE NAVEGAÇÃO
        # ==========================================
        
        st.divider()
        
        visao_infra = st.radio(
            "Selecione a perspectiva da infraestrutura:", 
            ["Tipo de Via", "Tipo de Pavimento", "Sinalização e Iluminação"],
            horizontal=True
        )

        st.write("") # Espaço extra

        # Renderiza apenas o gráfico selecionado ocupando a largura total
        if visao_infra == "Tipo de Via":
            st.plotly_chart(fig_via, use_container_width=True)
            
        elif visao_infra == "Tipo de Pavimento":
            st.plotly_chart(fig_pavimento, use_container_width=True)
            
        else:
            st.plotly_chart(fig_sinal, use_container_width=True)

    # ==========================================
    # ABAS 2 E 3 (TESTES E CONCLUSÕES)
    # ==========================================
    with tab2:
        st.subheader("Testes Estatísticos de Associação")
        
        colA, colB, colC = st.columns(3)
        with colA:
            st.info("""
            **1. Tipo da Via (Simples vs Não Simples)** * **H0:** A pavimentação e tipo da via não têm influência na gravidade.  
            * **Resultado:** Ao comparar a diferença entre os grupos “via simples” e “via não simples” na curva normal, tornou-se claro uma proporção de 5.225% com intervalo de confiança de 95%.  
            * **Conclusão:** Esse intervalo exclui a hipótese nula, logo a rejeitamos. A pavimentação da via foi descartada devido a discrepância enorme entre os tamanhos dos grupos.
            """)
        with colB:
            st.warning("""
            **2. Iluminação (Boa vs Não Há)** * **H0:** A iluminação não têm influência na gravidade.  
            * **Resultado:** Ao comparar a diferença, tornou-se claro uma proporção de 21.7%, com intervalo de confiança de 95%.  
            * **Conclusão:** Esse valor está muito acima da marca de 5%, e, portanto, não foi possível rejeitar a hipótese nula.
            """)
        with colC:
            st.error("""
            **3. Sinalização (Há vs Não Há)** * **H0:** A sinalização não têm influência na gravidade.  
            * **Resultado:** Ao comparar a diferença entre os grupos, percebe-se que essa diferença girava em torno de 0, ou seja, inclui a hipótese nula.  
            * **Conclusão:** Devido a isso não foi possível rejeitar a hipótese nula de que a sinalização isoladamente afeta a gravidade do acidente em BH.
            """)

    with tab3:
        st.success("""
        **Conclusões:**
        
        Os resultados determinam que o tipo de via é a variável de maior impacto na gravidade do acidente, e a única que permitiu rejeitar a hipótese nula. As condições das vias simples tornam acidentes graves mais propensos. 
        
        Quanto as variáveis de iluminação e sinalização, não foi observada evidência forte o suficiente para rejeitar a hipótese nula. Isso sugere que, em Belo Horizonte, acidentes tendem a independer da iluminação e sinalização, tendendo as duas a no geral serem boas.
        """)

def page_conclusao():
    st.title("Conclusões do Projeto")
    
    st.markdown("""
    ### Síntese dos Achados
    - **P1 Demografia:** Jovens concentram mais ocorrências, mas não os desfechos mais graves. O padrão de letalidade aparece nas faixas etárias mais altas. Um grupo pode dominar os registros por estar mais exposto, enquanto outro converte a mesma ocorrência em consequência mais séria.
    - **P2 Temporalidade:** O volume foca na saída do trabalho (18h) em dias úteis,principamente nas sexta-feiras mas a madrugada do final de semana carrega uma diferença significativa no risco proporcional de letalidade em acidentes.
    - **P3 Veículos:** Acidentes envolvendo veículos pesados possuem maiores taxas médias de vítimas em estado grave se comparado a veículos não pesados. Essa diferença fica ainda maior quando as vítimas são pedestres.
    - **P4 Infraestrutura:** Os resultados determinam que o tipo de via (simples vs dupla/múltipla) é a variável de maior impacto na gravidade do acidente, e a única que permitiu rejeitar a hipótese nula de infraestrutura.
    """)

# --- Roteamento ---
PAGES = {
    "Introdução": page_intro,
    "Tratamento das Bases": page_tratamento,
    "P1: Perfil Demográfico": page_pergunta_1,
    "P2: Tempo e Sazonalidade": page_pergunta_2,
    "P3: Veículos Envolvidos": page_pergunta_3,
    "P4: Infraestrutura": page_pergunta_4,
    "Conclusões Finais": page_conclusao
}

st.sidebar.title("Navegação")
selection = st.sidebar.radio("Ir para:", list(PAGES.keys()))
st.sidebar.divider()
st.sidebar.caption("TP de ICD - UFMG")

PAGES[selection]()
