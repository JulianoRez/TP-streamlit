import math
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import scipy.stats as ss
import streamlit as st

# --- Configurações da Página ---
st.set_page_config(
    page_title="ICD - Acidentes BH",
    page_icon="🚗",
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

ROOT = Path(__file__).resolve().parent

# Busca o diretório de dados independente do nome da pasta (procura pelo arquivo)
try:
    csv_file = next(ROOT.rglob("registros_limpo.csv"))
    DATA_DIR = csv_file.parent
except StopIteration:
    # Fallback se não encontrar o arquivo
    DATA_DIR = ROOT / "dados_limpos _alunos"


WEEKDAY_ORDER = ["SEGUNDA-FEIRA", "TERCA-FEIRA", "QUARTA-FEIRA", "QUINTA-FEIRA", "SEXTA-FEIRA", "SABADO", "DOMINGO"]
WEEKDAY_LABELS = {"SEGUNDA-FEIRA": "Seg", "TERCA-FEIRA": "Ter", "QUARTA-FEIRA": "Qua", "QUINTA-FEIRA": "Qui", "SEXTA-FEIRA": "Sex", "SABADO": "Sáb", "DOMINGO": "Dom"}
MONTH_LABELS = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}
COLOR_PALETTE = px.colors.qualitative.Prism

# --- Funções Auxiliares ---
def format_int(value): return f"{int(round(value)):,}".replace(",", ".")
def format_pct(value, digits=2): return f"{value * 100:.{digits}f}%".replace(".", ",")
def format_float(value, digits=2): return f"{value:.{digits}f}".replace(".", ",")

def proportion_ci(successes, total, z=1.96):
    if total == 0: return 0, 0, 0
    p = successes / total
    se = math.sqrt(p * (1 - p) / total)
    return p, max(0, p - z * se), min(1, p + z * se)

def difference_ci(successes_a, total_a, successes_b, total_b, z=1.96):
    if total_a == 0 or total_b == 0: return 0, 0, 0, 0
    p_a = successes_a / total_a
    p_b = successes_b / total_b
    diff = p_a - p_b
    se = math.sqrt(p_a * (1 - p_a) / total_a + p_b * (1 - p_b) / total_b)
    z_stat = diff / se if se > 0 else 0
    return diff, diff - z * se, diff + z * se, z_stat

# --- Carregamento de Dados ---
@st.cache_data(show_spinner=False)
def load_registros(columns=None):
    df = pd.read_csv(DATA_DIR / "registros_limpo.csv", sep=";", usecols=columns, low_memory=False)
    for col in ["ano_fato", "mes_numerico_fato", "hora_fato"]:
        if col in df.columns: df[col] = pd.to_numeric(df[col], errors="coerce")
    if "data_fato" in df.columns: df["data_fato"] = pd.to_datetime(df["data_fato"], errors="coerce")
    return df

@st.cache_data(show_spinner=False)
def load_vitimas():
    path_semi = DATA_DIR / "vitimas_limpo2.csv"
    df = pd.read_csv(path_semi, sep=";", low_memory=False) if path_semi.exists() else pd.read_csv(DATA_DIR / "vitimas_limpo.csv", sep=",", low_memory=False)
    unnamed = [c for c in df.columns if c.lower().startswith("unnamed") or c == ""]
    if unnamed: df = df.drop(columns=unnamed)
    df["valor_idade_aparente"] = pd.to_numeric(df["valor_idade_aparente"], errors="coerce")
    df["grave_ou_fatal"] = df["condicao_fisica_descricao"].isin(["GRAVES OU INCONSCIENTE", "FATAL"]).astype(int)
    return df

@st.cache_data(show_spinner=False)
def load_condicoes(): return pd.read_csv(DATA_DIR / "condicoes_limpa.csv", sep=";", low_memory=False)

@st.cache_data(show_spinner=False)
def load_via(): return pd.read_csv(DATA_DIR / "via_limpo.csv", sep=";", low_memory=False)

@st.cache_data(show_spinner=False)
def load_vehicle_flags():
    motos = {"MOTOCICLETA", "MOTONETA", "CICLOMOTOR"}
    pesados = {"CAMINHAO", "ONIBUS", "MICROONIBUS"}
    parts = []
    for chunk in pd.read_csv(DATA_DIR / "veiculos_limpo.csv", sep=";", usecols=["numero_ocorrencia_associado", "tipo_veiculo_descricao_longa"], chunksize=500_000, low_memory=False):
        tipo = chunk["tipo_veiculo_descricao_longa"].fillna("").str.upper()
        flags = pd.DataFrame({
            "numero_ocorrencia_associado": chunk["numero_ocorrencia_associado"], 
            "envolve_moto": tipo.isin(motos).astype(int), 
            "envolve_pesado": tipo.isin(pesados).astype(int)
        })
        parts.append(flags.groupby("numero_ocorrencia_associado", as_index=False).max())
    return pd.concat(parts, ignore_index=True).groupby("numero_ocorrencia_associado", as_index=False).max()

# --- Páginas ---
def page_intro():
    st.markdown('<p class="main-header">Acidentes de Trânsito em Belo Horizonte</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Dashboard Analítico - Introdução à Ciência de Dados</p>', unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Registros Processados", format_int(1040217), delta="2012 a 2025", delta_color="off")
    with col2: st.metric("Vítimas Analisadas", format_int(182739))
    with col3: st.metric("Condições da Via", format_int(179492))
    with col4: st.metric("Veículos Envolvidos", "6.5M+")
    
    st.divider()
    
    st.markdown("### 🎯 Perguntas de Pesquisa")
    colA, colB = st.columns(2)
    with colA:
        st.info("**P1:** Qual perfil demográfico apresenta maior proporção de vítimas graves ou fatais?")
        st.success("**P2:** Como os acidentes se distribuem no tempo e é possível prever volumes futuros?")
    with colB:
        st.warning("**P3:** O tipo ou porte do veículo influencia a gravidade das vítimas?")
        st.error("**P4:** Problemas de infraestrutura influenciam a gravidade dos acidentes?")

def page_tratamento():
    st.title("🛠️ Tratamento das Bases")

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
    st.title("👤 P1: Perfil Demográfico")
    
    tab1, tab2, tab3 = st.tabs(["📊 Exploração", "⚖️ Testes e IC", "💡 Conclusões"])
    
    with tab1:
        st.write("Visualização da proporção de vítimas graves ou fatais por perfil.")
        
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
        
        sucessos_perfil, total_perfil = 1127, 13815
        sucessos_outros, total_outros = 6902, 80557
        
        colA, colB, colC = st.columns(3)
        colA.metric("Homens pardos 18-25 (Graves/Total)", f"{format_int(sucessos_perfil)} / {format_int(total_perfil)}")
        colB.metric("Taxa Observada (Grupo)", "8,16%")
        colC.metric("Taxa Demais Perfis", "8,57%")
        
        st.info("**Estatística Z:** -1.5960 | **p-valor (unilateral):** 0.9448")
        st.warning("Não rejeitamos a Hipótese Nula (H0). O p-valor ficou bem acima de 5%. A proporção observada no grupo de interesse ficou abaixo da dos demais perfis.")

    with tab3:
        st.success("""
        **Conclusão:**
        Jovens concentram mais ocorrências, mas não os desfechos mais graves. E como observado esse padrão aparece nas faixas etárias mais altas, o que faz sentido: seres humanos mais jovens concentram mais ocorrências, porém o padrão de letalidade aparece nas faixas etárias mais altas. E isso também faz sentido, pessoas mais velhas toleram menos o trauma e se recuperam com mais dificuldade. A distinção importa porque volume e gravidade não andam juntos. Um grupo pode dominar os registros por estar mais exposto, enquanto outro, menos frequente, converte a mesma ocorrência em consequência mais séria. Ignorar essa diferença distorce tanto a leitura dos dados quanto as prioridades de intervenção.
        """)

def page_pergunta_2():
    st.title("⏳ P2: Distribuição Temporal")
    
    registros = load_registros(columns=["numero_ocorrencia_associado", "ano_fato", "mes_numerico_fato", "data_fato", "dia_da_semana", "hora_fato"]).dropna()
    for c in ["ano_fato", "mes_numerico_fato", "hora_fato"]: registros[c] = registros[c].astype(int)
    
    hora = registros.groupby("hora_fato").size().reset_index(name="ocorrencias")
    
    dias_semana = registros[["data_fato", "dia_da_semana"]].drop_duplicates().groupby("dia_da_semana").size()
    semana = (registros.groupby("dia_da_semana").size() / dias_semana).reset_index(name="media_diaria")
    semana["ordem"] = semana["dia_da_semana"].map({d: i for i, d in enumerate(WEEKDAY_ORDER)})
    semana["dia"] = semana["dia_da_semana"].map(WEEKDAY_LABELS)
    semana = semana.sort_values("ordem")
    
    tab1, tab2, tab3 = st.tabs(["📈 Análise Exploratória", "⚖️ Testes e IC", "💡 Conclusões"])
    
    with tab1:
        st.write("Agrupamos os acidentes por hora e dia da semana. Usamos **médias diárias** para evitar vieses de calendário.")
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(hora, x="hora_fato", y="ocorrencias", title="Volume por Hora (Pico em Vermelho)", template="plotly_white")
            fig1.add_vrect(x0=16.5, x1=19.5, fillcolor="red", opacity=0.15, line_width=0)
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.bar(semana, x="dia", y="media_diaria", title="Média Diária por Dia da Semana", template="plotly_white", color_discrete_sequence=[COLOR_PALETTE[2]])
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.subheader("Validação Estatística das Hipóteses")
        total = len(registros)
        rush = registros["hora_fato"].between(17, 19).sum()
        p_rush, rush_low, rush_high = proportion_ci(rush, total)
        
        weekend = registros["dia_da_semana"].isin(["SABADO", "DOMINGO"])
        night = registros["hora_fato"].between(0, 5)
        weekend_night = (weekend & night).sum()
        weekday_night = ((~weekend) & night).sum()
        diff, diff_low, diff_high, z_stat_mad = difference_ci(weekend_night, weekend.sum(), weekday_night, (~weekend).sum())
        
        colA, colB = st.columns(2)
        with colA:
            st.info(f"""
            **Teste 1: Horário de Pico (17h-19h)**
            * **H0:** Proporção uniforme (esperado 12,50%).
            * **H1:** Proporção > 12,50%.
            * **Resultado:** Observado **{format_pct(p_rush)}**.
            * **IC 95%:** [{format_pct(rush_low)} - {format_pct(rush_high)}].
            * **Conclusão:** Rejeitamos H0 ($p < 0.001$). Há concentração estatisticamente relevante.
            """)
        with colB:
            st.warning(f"""
            **Teste 2: Madrugada no Fim de Semana (00h-05h)**
            * **H0:** Proporção igual em dias úteis e fds.
            * **H1:** Proporção é maior nos fins de semana.
            * **Diferença:** **{format_pct(diff)}** a mais na madrugada do final de semana.
            * **IC 95%:** [{format_pct(diff_low)} - {format_pct(diff_high)}].
            * **Conclusão:** Rejeitamos H0 ($p < 0.001$). Madrugadas de fds são proporcionalmente mais perigosas.
            """)

    with tab3:
        st.success("""
        **Conclusões da Pergunta 2:**
        A distribuição não é aleatória no tempo. O volume cresce fortemente no fim da tarde, na saída do trabalho (17h a 19h). A sexta-feira é o dia com maior média diária absoluta. No entanto, embora o fim de semana tenha um volume total menor de acidentes, a madrugada de fim de semana possui um peso de gravidade proporcional extremamente alto em comparação com dias úteis.
        """)

def page_pergunta_3():
    st.title("🚛 P3: Tipo de Veículo vs Severidade")
    
    tab1, tab2, tab3 = st.tabs(["📊 Análise Geral", "⚖️ Testes (A/B e Bootstrap)", "💡 Conclusões"])
    with tab1:
        st.write("Análise da relação entre configuração veicular (porte pesado e motos) e a presença de vítimas graves ou fatais.")
        st.write("O grupo uniu as bases de veículos e de vítimas e agregou veículos como 'PESADO' e 'NÃO PESADO', separando-se condutores e pedestres para mensurar o impacto das colisões.")
        
        st.info("O agrupamento identificou veículos de grande massa (Ônibus, Micro-ônibus e Caminhões) versus demais veículos, e testou a hipótese do impacto ser pior com veículos pesados e com motocicletas.")

    with tab2:
        st.subheader("Testes de Hipótese (Diferença nas Taxas Médias de Gravidade)")

        colA, colB, colC = st.columns(3)
        with colA:
            st.info("""
            **1. Veículos Pesados (Pedestres)**  
            * **H0:** Acidentes com pesados e não pesados têm taxas iguais de vítimas em estado grave.  
            * **H1:** Pesados possuem maiores proporções.  
            * **Resultado:** Diferença média observada é *positiva*.  
            * **Conclusão:** Rejeitamos H0. A hipótese alternativa é verdadeira, pesados são piores, especialmente para pedestres desprotegidos.
            """)
        with colB:
            st.warning("""
            **2. Motos (Condutores e Passageiros)**  
            * **H0:** Acidentes com motos ou outros veículos têm taxas iguais.  
            * **H1:** Motos possuem maior proporção de feridos graves.  
            * **Resultado:** A diferença média observada no Bootstrap foi *negativa*.  
            * **Conclusão:** Rejeitamos H0, porém a média menor *contraria a H1*. Em média, as taxas de ocorrências exclusivas de motos tenderam a não ser superiores que o grupo de controle (veículos não motos).
            """)
        with colC:
            st.success("""
            **Uso do Bootstrap**  
            Para a comparação da diferença entre proporções de vítimas pesadas e não pesadas, foi construída uma distribuição com 5.000 subamostras.  
            Os limites de 2,5% e 97,5% da distribuição do Bootstrap excluíram o zero perfeitamente (Hipótese Nula).
            """)

    with tab3:
        st.success("""
        **Conclusões:**
        Com os resultados, foi possível concluir que os acidentes envolvendo veículos pesados possuem maiores taxas médias de vítimas em estado grave se comparado a veículos não pesados. Essa diferença fica ainda maior quando as vítimas são pedestres. Ainda, vale ressaltar que não foi possível concluir que, em acidentes envolvendo condutores ou passageiros, as motos tendem a possuir maiores proporções médias deles em estado grave se comparado a veículos que não são motos. O resultado para veículos pesados condisse com nossa suposição, uma vez que, fisicamente, um corpo acelerado com maior massa produz maior força sobre um objeto. Por outro lado, o resultado para motos não condisse com o esperado. Parece, então, que o fator porte do veículo possui maior associação com a maior proporção média de vítimas em estado grave.
        """)

def page_pergunta_4():
    st.title("🛣️ P4: Infraestrutura da Via")
    
    tab1, tab2, tab3 = st.tabs(["📊 Análise Exploratória", "⚖️ Testes de Hipótese (A/B)", "💡 Conclusões"])
    with tab1:
        st.write("A análise focou em três vertentes da infraestrutura em Belo Horizonte: Capacidade da Via, Luminosidade e Sinalização.")
        st.markdown("""
        - A maioria dos acidentes ocorre no asfalto, o que pode dar uma "falsa sensação de segurança" (Falta de Atenção).
        - A sinalização de trânsito constou como 'BOA' em mais de 60% dos casos.
        - Pistas de mão simples representam maioria de colisões frontais ou acidentes severos.
        """)

    with tab2:
        st.subheader("Testes Estatísticos de Associação")
        
        colA, colB, colC = st.columns(3)
        with colA:
            st.info("""
            **1. Tipo da Via (Capacidade)**  
            * **H0:** O tipo de via não afeta a gravidade.  
            * **Resultado:** Diferença clara entre via simples e vias não simples.  
            * **p-valor/IC:** Proporção de diferença indicou significância estatística (p-valor < 5%).  
            * **Conclusão:** Rejeitamos H0. Pistas simples tornam os acidentes mais propensos à severidade (ex: choques frontais).
            """)
        with colB:
            st.warning("""
            **2. Luminosidade (Dia vs Má iluminação)**  
            * **H0:** Iluminação não afeta a gravidade.  
            * **Resultado:** p-valor atingiu a marca de 21.7%.  
            * **Conclusão:** Como 21.7% > 5%, não foi possível rejeitar H0. Diferenças de iluminação sozinhas podem ser fruto do acaso.
            """)
        with colC:
            st.error("""
            **3. Sinalização (Boa vs Não Há/Ruim)**  
            * **H0:** A sinalização não afeta a gravidade.  
            * **Resultado:** A diferença nos testes A/B entre os dois grupos rodou muito próxima do zero.  
            * **Conclusão:** O IC engloba o zero. Não rejeitamos a H0 de que a sinalização isoladamente afeta a gravidade do acidente em BH.
            """)

    with tab3:
        st.success("""
        **Conclusões:**
        Os resultados determinam que o **tipo de via (pista simples)** é a variável de maior impacto na gravidade do acidente, permitindo rejeitar a hipótese nula com facilidade.
        Quanto às variáveis de iluminação e sinalização, não houve evidência matemática na amostra macro de BH para associá-las de forma conclusiva com letalidade, possivelmente devido à infraestrutura base da capital ou ao fato de condutores ajustarem a velocidade na escuridão.
        """)

def page_modelos():
    st.title("🤖 Modelos de Machine Learning")
    
    # tab1, tab2 = st.tabs(["📈 Regressão (Volume Mensal)", "🔮 Classificação (Risco Grave/Fatal)"])
    
    # with tab1:
    #     from sklearn.linear_model import LinearRegression
    #     from sklearn.metrics import mean_absolute_error, r2_score
        
    #     st.write("Criamos um modelo para tentar prever o número absoluto de acidentes em um mês, usando o Tempo (tendência) e o Mês (Sazonalidade).")
        
    #     reg_df = load_registros(columns=["ano_fato", "mes_numerico_fato"]).dropna().astype(int)
    #     df_mensal = reg_df.groupby(["ano_fato", "mes_numerico_fato"]).size().reset_index(name="acidentes").sort_values(["ano_fato", "mes_numerico_fato"]).reset_index(drop=True)
    #     df_mensal["tempo"] = np.arange(1, len(df_mensal) + 1)
    #     df_mensal["data"] = pd.to_datetime(dict(year=df_mensal["ano_fato"], month=df_mensal["mes_numerico_fato"], day=1))
        
    #     X = pd.concat([df_mensal[["tempo"]], pd.get_dummies(df_mensal["mes_numerico_fato"], prefix="mes", drop_first=True)], axis=1)
    #     y = df_mensal["acidentes"]
        
    #     train_size = max(len(df_mensal) - 24, 1)
    #     X_train, X_test, y_train, y_test = X.iloc[:train_size], X.iloc[train_size:], y.iloc[:train_size], y.iloc[train_size:]
        
    #     model = LinearRegression().fit(X_train, y_train)
    #     pred = model.predict(X_test)
        
    #     col1, col2, col3 = st.columns(3)
    #     col1.metric("MAE (Erro Médio Absoluto)", format_float(mean_absolute_error(y_test, pred), 1))
    #     col2.metric("R² Teste", format_float(r2_score(y_test, pred), 2))
        
    #     fig = go.Figure()
    #     fig.add_trace(go.Scatter(x=df_mensal["data"], y=df_mensal["acidentes"], name="Real", line=dict(color="gray")))
    #     fig.add_trace(go.Scatter(x=df_mensal.iloc[train_size:]["data"], y=pred, name="Previsto", line=dict(color="red", dash="dash")))
    #     fig.update_layout(title="Regressão Linear Múltipla (Treino/Teste)", template="plotly_white")
    #     st.plotly_chart(fig, use_container_width=True)
        
    #     with st.expander("Ver Importância das Variáveis (Coeficientes)"):
    #         coef_df = pd.DataFrame({"Variável": X.columns, "Coeficiente": model.coef_}).sort_values("Coeficiente")
    #         st.dataframe(coef_df, use_container_width=True)

    # with tab2:
    #     from sklearn.compose import ColumnTransformer
    #     from sklearn.impute import SimpleImputer
    #     from sklearn.linear_model import LogisticRegression
    #     from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    #     from sklearn.model_selection import train_test_split
    #     from sklearn.pipeline import Pipeline
    #     from sklearn.preprocessing import OneHotEncoder, StandardScaler
        
    #     st.write("Regressão Logística para classificar se a vítima sairá com lesões Graves/Fatais baseado no contexto do choque.")
        
    #     df_clf = load_vitimas()[["numero_ocorrencia_associado", "valor_idade_aparente", "codigo_sexo", "grave_ou_fatal", "condicao_fisica_descricao"]].dropna(subset=["grave_ou_fatal"])
    #     df_clf = df_clf[~df_clf["condicao_fisica_descricao"].eq("GRAU DA LESAO - IGNORADO")].sample(50000, random_state=42) # Amostra para rodar rápido
        
    #     reg = load_registros(columns=["numero_ocorrencia_associado", "hora_fato", "dia_da_semana"])
    #     df_ml = df_clf.merge(reg, on="numero_ocorrencia_associado", how="left").dropna()
        
    #     X_clf = df_ml[["valor_idade_aparente", "hora_fato", "codigo_sexo", "dia_da_semana"]]
    #     y_clf = df_ml["grave_ou_fatal"].astype(int)
        
    #     X_tr, X_te, y_tr, y_te = train_test_split(X_clf, y_clf, test_size=0.25, random_state=42, stratify=y_clf)
        
    #     preprocessor = ColumnTransformer(transformers=[
    #         ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), ["valor_idade_aparente", "hora_fato"]),
    #         ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), ["codigo_sexo", "dia_da_semana"])
    #     ])
        
    #     clf = Pipeline(steps=[("prep", preprocessor), ("logreg", LogisticRegression(class_weight="balanced", max_iter=500))])
    #     clf.fit(X_tr, y_tr)
    #     y_pred = clf.predict(X_te)
        
    #     cA, cB, cC, cD = st.columns(4)
    #     cA.metric("Acurácia", format_pct(accuracy_score(y_te, y_pred)))
    #     cB.metric("Precisão", format_pct(precision_score(y_te, y_pred, zero_division=0)))
    #     cC.metric("Recall (Sensibilidade)", format_pct(recall_score(y_te, y_pred, zero_division=0)))
    #     cD.metric("F1-Score", format_pct(f1_score(y_te, y_pred, zero_division=0)))
        
    #     st.info("Como a base é desbalanceada (poucos acidentes graves em relação ao total), usamos `class_weight='balanced'`. O Recall alto mostra que o modelo consegue identificar boa parte dos acidentes graves, mesmo que erre alguns leves (baixa precisão).")

def page_conclusao():
    st.title("🎯 Conclusões da Pesquisa")
    st.markdown("""
    ### Síntese dos Achados
    - **P1 Demografia:** O grupo demográfico influencia fortemente a proporção de letalidade, destacando-se uma vulnerabilidade extrema nas faixas etárias de idosos. A hipótese restrita a homens jovens pardos foi rejeitada (z = -1.59, p = 0.94).
    - **P2 Temporalidade:** O volume absoluto foca na saída do trabalho (18h) em dias úteis, mas a madrugada do final de semana carrega uma diferença significativa no risco de letalidade em acidentes.
    - **P3 Veículos:** A inércia domina o fator de gravidade: acidentes cruzando pedestres e veículos pesados são exponencialmente mais letais. O modelo A/B demonstrou significância estatística que o peso veicular afeta as vítimas, principalmente pedestres.
    - **P4 Infraestrutura:** Pistas simples indicam maior risco severo de batidas. Por outro lado, iluminação e sinalização deficiente sozinhas não foram suficientes para sustentar a rejeição da hipótese nula na base como um todo.
    
    """)
# --- Roteamento ---
PAGES = {
    " Introdução": page_intro,
    " Tratamento das Bases": page_tratamento,
    " P1: Perfil Demográfico": page_pergunta_1,
    " P2: Tempo e Sazonalidade": page_pergunta_2,
    " P3: Veículos Envolvidos": page_pergunta_3,
    " P4: Infraestrutura": page_pergunta_4,
    " Modelos (Classif. & Reg.)": page_modelos,
    " Conclusões": page_conclusao
}

st.sidebar.title("Navegação")
selection = st.sidebar.radio("Ir para:", list(PAGES.keys()))
st.sidebar.divider()
st.sidebar.caption("TP de ICD")

PAGES[selection]()
