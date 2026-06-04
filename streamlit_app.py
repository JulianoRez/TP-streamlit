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
    st.markdown('<p class="sub-header">Dashboard Analítico - Introdução à Ciência de Dados</p>', unsafe_allow_html=True)
    
    st.write("""
        Bem-vindo ao dashboard interativo do nosso estudo sobre acidentes de trânsito.
        Este projeto integra diferentes bases públicas para extrair padrões estatísticos reais sobre 
        letalidade, sazonalidade e fatores de risco no trânsito da capital mineira.
    """)
    
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
    st.markdown("Esta seção detalha o fluxo de limpeza e padronização dos dados utilizados para cada uma das perguntas de pesquisa, conforme os scripts do projeto.")

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
    
    with tab1:
        st.write("Visualização da proporção de vítimas graves ou fatais por perfil, conforme apurado na limpeza do grupo (removidos ignorados e nulos).")
        
        sexo = pd.DataFrame({"Sexo": ["Homens", "Mulheres"], "Taxa": [0.0904, 0.0702]})
        cor = pd.DataFrame({"Cor/Raça": ["Negra", "Preto", "Parda", "Branca"], "Taxa": [0.0972, 0.0860, 0.0855, 0.0797]})
        faixa = pd.DataFrame({"Faixa Etária": ["80+", "70-79", "60-69", "18-29"], "Taxa": [0.1608, 0.1287, 0.1148, 0.0761]})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            fig1 = px.bar(sexo, x="Sexo", y="Taxa", text=sexo["Taxa"].apply(lambda x: format_pct(x, 2)), 
                          title="Gravidade por Sexo", template="plotly_white", color_discrete_sequence=[COLOR_PALETTE[0]])
            fig1.update_layout(yaxis_tickformat=".0%")
            st.plotly_chart(fig1, use_container_width=True)
            
        with col2:
            fig2 = px.bar(cor, x="Cor/Raça", y="Taxa", text=cor["Taxa"].apply(lambda x: format_pct(x, 2)), 
                          title="Gravidade por Cor/Raça", template="plotly_white", color_discrete_sequence=[COLOR_PALETTE[1]])
            fig2.update_layout(yaxis_tickformat=".0%")
            st.plotly_chart(fig2, use_container_width=True)
            
        with col3:
            fig3 = px.bar(faixa, x="Faixa Etária", y="Taxa", text=faixa["Taxa"].apply(lambda x: format_pct(x, 2)), 
                          title="Gravidade por Faixa Etária", template="plotly_white", color_discrete_sequence=[COLOR_PALETTE[2]])
            fig3.update_layout(yaxis_tickformat=".0%")
            st.plotly_chart(fig3, use_container_width=True)

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
        st.write("Agrupamos os acidentes por hora, dia da semana e mês. Usamos **médias diárias** para evitar vieses de calendário.")
        
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

def page_pergunta_3():
    st.title("Pergunta 3: Tipo de Veículo vs Severidade")
    
    tab1, tab2, tab3 = st.tabs(["Análise Geral", "Testes Específicos (A/B e Bootstrap)", "Conclusões"])
    with tab1:
        st.write("Análise da relação entre configuração veicular (porte pesado e motos) e a presença de vítimas graves ou fatais.")
        st.info("O agrupamento identificou veículos de grande massa (Ônibus, Micro-ônibus e Caminhões) versus demais veículos, e testou a hipótese do impacto ser pior com veículos pesados e com motocicletas.")
        
        grupos = pd.DataFrame({
            "Envolvimento": ["Pesados (Geral)", "Pesados (Pedestres)", "Motos (Condutores/Passageiros)"],
            "Diferença Observada Média": ["Positiva (+)", "Positiva (++)", "Negativa (-)"]
        })
        st.table(grupos)

    with tab2:
        st.subheader("Testes de Hipótese (Diferença nas Taxas Médias de Gravidade)")

        colA, colB, colC = st.columns(3)
        with colA:
            st.info("""
            **1. Veículos Pesados (Pedestres)**  
            * **H0:** Acidentes que envolvem veículos pesados e não pesados tendem a, em média, possuir iguais proporções de vítimas pedestres em estado grave.  
            * **HA:** Acidentes que envolvem veículos pesados tendem a, em média, possuir maiores proporções de vítimas pedestres em estado grave do que os demais tipos de veículo.  
            * **Resultado:** Com esse teste, nossa hipótese nula pode ser rejeitada, pois ela não pertence ao IC mostrado. A diferença média observada é positiva, o que nos permite tomar a hipótese alternativa como verdadeira.
            """)
        with colB:
            st.warning("""
            **2. Motos (Condutores e Passageiros)**  
            * **H0:** Acidentes que envolvem motos e não motos tendem a, em média, possuir iguais proporções de vítimas condutoras ou passageiras em estado grave.  
            * **HA:** Acidentes que envolvem motos tendem a, em média, possuir maiores proporções de vítimas condutoras ou passageiras em estado grave do que os demais tipos de veículo.  
            * **Resultado:** A hipótese nula é rejeitada, pois ela não pertence ao IC. Todavia, a diferença média observada é negativa, o que não está de acordo com a hipótese alternativa, pois, para tanto, a média devia ser positiva. Acidentes exclusivos de motos e suas vítimas possuem, em média, menores taxas em estado grave, quando comparados a veículos não motos.
            """)
        with colC:
            st.success("""
            **Uso do Bootstrap**  
            Para a comparação da diferença entre proporções de vítimas pesadas e não pesadas, foi construída uma distribuição Bootstrap de 5.000 subamostras.  
            Os limites de 2,5% e 97,5% da distribuição do Bootstrap excluíram o zero (Hipótese Nula), confirmando estatisticamente as observações com um alto rigor de amostragem.
            """)

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
        st.write("A análise focou em três vertentes da infraestrutura em Belo Horizonte: Capacidade da Via, Luminosidade e Sinalização.")
        
        pav_df = pd.DataFrame({"Tipo de Pavimento": ["Asfalto", "Não Informado", "Calçamento", "Concreto", "Outros", "Terra"], "Porcentagem": [95.59, 1.97, 1.17, 0.66, 0.53, 0.04]}).sort_values("Porcentagem")
        via_df = pd.DataFrame({"Tipo de Via": ["Pista Simples", "Pista Dupla", "Pista Múltipla", "Não Informado"], "Porcentagem": [52.87, 26.28, 20.20, 0.66]}).sort_values("Porcentagem")
        sin_df = pd.DataFrame({"Sinalização": ["Boa", "Não Há", "Em Más Condições", "Não Informado", "Irregular"], "Porcentagem": [74.63, 16.83, 3.56, 3.20, 1.78]}).sort_values("Porcentagem")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            fig1 = px.bar(pav_df, y="Tipo de Pavimento", x="Porcentagem", orientation='h', title="Pavimento (Asfalto absoluto)", template="plotly_white")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.bar(via_df, y="Tipo de Via", x="Porcentagem", orientation='h', title="Tipo da Pista", template="plotly_white")
            st.plotly_chart(fig2, use_container_width=True)
        with col3:
            fig3 = px.bar(sin_df, y="Sinalização", x="Porcentagem", orientation='h', title="Sinalização", template="plotly_white")
            st.plotly_chart(fig3, use_container_width=True)
            
        st.markdown("""
        1. A maioria esmagadora dos acidentes acontecem no asfalto, podendo levar a insights sobre a falsa sensação de segurança.
        2. Outra maioria exorbitante é de acidentes em pistas simples, o que nos leva a possivelmente entender como essas pistas levam a mais colisões frontais em ultrapassagens.
        3. A sinalização é predominantemente boa, compondo mais de 60% dos casos de acidentes. Isso indica que a falta de sinalização não é uma das causas primárias para os acidentes.
        """)

    with tab2:
        st.subheader("Testes Estatísticos de Associação")
        
        colA, colB, colC = st.columns(3)
        with colA:
            st.info("""
            **1. Tipo da Via (Simples vs Não Simples)**  
            * **H0:** A pavimentação e tipo da via não têm influência na gravidade.  
            * **Resultado:** Ao comparar a diferença entre os grupos “via simples” e “via não simples” na curva normal, tornou-se claro uma proporção de 5.225% com intervalo de confiança de 95%.  
            * **Conclusão:** Esse intervalo exclui a hipótese nula, logo a rejeitamos. A pavimentação da via foi descartada devido a discrepância enorme entre os tamanhos dos grupos.
            """)
        with colB:
            st.warning("""
            **2. Iluminação (Boa vs Não Há)**  
            * **H0:** A iluminação não têm influência na gravidade.  
            * **Resultado:** Ao comparar a diferença, tornou-se claro uma proporção de 21.7%, com intervalo de confiança de 95%.  
            * **Conclusão:** Esse valor está muito acima da marca de 5%, e, portanto, não foi possível rejeitar a hipótese nula.
            """)
        with colC:
            st.error("""
            **3. Sinalização (Há vs Não Há)**  
            * **H0:** A sinalização não têm influência na gravidade.  
            * **Resultado:** Ao comparar a diferença entre os grupos, percebe-se que essa diferença girava em torno de 0, ou seja, inclui a hipótese nula.  
            * **Conclusão:** Devido a isso não foi possível rejeitar a hipótese nula de que a sinalização isoladamente afeta a gravidade do acidente em BH.
            """)

    with tab3:
        st.success("""
        **Conclusões:**
        Os resultados determinam que o tipo de via é a variável de maior impacto na gravidade do acidente, e a única que permitiu rejeitar a hipótese nula. As condições das vias simples tornam acidentes graves mais propensos. Quanto as variáveis de iluminação e sinalização, não foi observada evidência forte o suficiente para rejeitar a hipótese nula. Isso sugere que, em Belo Horizonte, acidentes tendem a independer da iluminação e sinalização, tendendo as duas a no geral serem boas.
        """)

def page_conclusao():
    st.title("Conclusões e Modelos da Pesquisa")
    
    tab1, tab2 = st.tabs(["O que aprendemos", "Proposta de Machine Learning"])
    
    with tab1:
        st.markdown("""
        ### Síntese dos Achados
        - **P1 Demografia:** Jovens concentram mais ocorrências, mas não os desfechos mais graves. O padrão de letalidade aparece nas faixas etárias mais altas. Um grupo pode dominar os registros por estar mais exposto, enquanto outro converte a mesma ocorrência em consequência mais séria.
        - **P2 Temporalidade:** O volume absoluto foca na saída do trabalho (18h) em dias úteis, mas a madrugada do final de semana carrega uma diferença significativa no risco proporcional de letalidade em acidentes.
        - **P3 Veículos:** A inércia domina o fator de gravidade: acidentes envolvendo veículos pesados possuem maiores taxas médias de vítimas em estado grave se comparado a veículos não pesados. Essa diferença fica ainda maior quando as vítimas são pedestres.
        - **P4 Infraestrutura:** Os resultados determinam que o tipo de via (simples vs dupla/múltipla) é a variável de maior impacto na gravidade do acidente, e a única que permitiu rejeitar a hipótese nula de infraestrutura.
        """)
        
    with tab2:
        st.markdown("""
        ### Discussão: O que poderíamos treinar usando Aprendizado de Máquina?
        O monitor apontou que temos a liberdade de aplicar classificações ou regressões que façam sentido para o contexto do trabalho. Observando as nossas conclusões estatísticas, sugerimos duas abordagens fortes de Inteligência Artificial:

        #### 1. Classificador Logístico: O "Alerta" para o Samu
        Como os Testes A/B e o Bootstrap comprovaram que Tipo de Veículo (Inércia) e Idade da Vítima (Fragilidade) são chaves estatísticas para desfechos severos, a primeira recomendação é usar um algoritmo de Classificação Binária (como Regressão Logística ou Árvore de Decisão).
        - **Target:** `Grave_ou_Fatal` (1 ou 0).
        - **Features:** Hora, Tipo de Veículo (Pesado = 1), Idade da Vítima.
        - **Uso real:** O centro de despacho de ambulâncias recebe a notificação da batida e o modelo cospe: "Probabilidade de vítima grave: 82%".

        #### 2. Regressão Linear Múltipla: Sazonalidade Pós-Pandemia
        Vimos na Pergunta 2 que as séries anuais e médias mensais flutuam muito. Mas será que dá para prever os números brutos do mês que vem?
        - **Target:** `Quantidade de Acidentes`.
        - **Features:** Uma variável `Tempo` sequencial para capturar crescimento da frota, e *Dummies* de `Mês` (Jan a Dez) para que o modelo entenda que Novembro é sazonalmente pior que Janeiro.
        - **Métrica:** Avaliaria o erro absoluto médio (MAE). Serviria para o planejamento de férias da Polícia de Trânsito ou campanhas publicitárias preventivas.
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
st.sidebar.caption("TP de ICD - UFMG | Dashboards com Streamlit e Plotly")

PAGES[selection]()
