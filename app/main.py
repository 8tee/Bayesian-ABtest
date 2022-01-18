import streamlit as st
import pandas as pd
from datetime import timedelta
import bayes
# from preprocess import preprocess
st.set_page_config(layout="wide", page_title= "ABtest", page_icon= "random")
st.title("A/B test")

st.markdown(""" <style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style> """, unsafe_allow_html=True)

# try
data_file = st.container()
with data_file:
  uploaded_file = st.file_uploader("Choose a raw data file")
  demo_data = st.checkbox("Use a demo dataset")
  if uploaded_file is None:
    if demo_data:
      df = pd.read_csv('data/ab_data.csv')
    else:
      df = pd.read_csv(uploaded_file)
  else:
    st.info("Please upload raw data file or use demo dataset")


# Date range
df['timestamp'] = pd.to_datetime(df['timestamp']).dt.date
min_date = df['timestamp'].min()
max_date =  df['timestamp'].max()
install_date_choice = st.sidebar.date_input('Select Date Range', (min_date, max_date))


# Filter data
df = df.loc[
  (df.timestamp >= install_date_choice[0]) 
  & (df.timestamp <= install_date_choice[1])
]

st.text("Shape of dataframe", df.shape)
st.write(df)

st.header('Experiment')
control = st.text_input('Control name', 'control')
variation = st.text_input('Variation name', 'treatment')

ab_list = [control, variation]
# add the key choices_len to the session_state
if not "choices_len" in st.session_state:
  st.session_state["choices_len"] = 0

# c_up contains the form
# c_down contains the add and remove buttons
c_up = st.container()
c_down = st.container()

with c_up:
  with st.form("myForm"):
    c1 = st.container() # c1 contains choices
    c2 = st.container() # c2 contains submit button
    with c2:
      st.form_submit_button("Submit")

with c_down:
  col_l, _, col_r = st.columns((2,1,2))
  with col_l:
    if st.button("Add Metric"):
      st.session_state["choices_len"] += 1

  with col_r:
    if st.button("Remove Metric") and st.session_state["choices_len"] > 1:
      st.session_state["choices_len"] -= 1
      st.session_state.pop(f'{st.session_state["choices_len"]}')


for x in range(st.session_state["choices_len"]): # create many choices
  with c1:
    st.text_input("Metric", key="metric" + f"{x}")
    st.radio("Type", key="type" + f"{x}", options=('Duration', 'Count', 'Binomial'))


# reads values from the session_state using the key.
# also doesn't return an option if the value is empty
metrics = st.multiselect("Goal Metrics", options=[
  st.session_state["metric" + f"{x}"]\
  for x in range(st.session_state["choices_len"])\
  if not st.session_state["metric" + f"{x}"] == ''])


day_win = 3
from_date = df.timestamp.min().strftime('%d/%m')
to_date = (df.timestamp.max() - timedelta(days = day_win + 1)).strftime('%d/%m')

def preprocess(data, metrics, ab_list,  day_window = 3):
  data = data.query('group in @ab_list')
  dim = data.groupby('user_id')['group'].max().reset_index()
  fact = data.groupby('user_id')[metrics].sum()
  data = dim.merge(fact, on ='user_id')
  return data

data = preprocess(df, metrics, ab_list, day_window = day_win)
descriptive_metric = []
number_user = data.groupby('group').agg({'user_id':pd.Series.nunique})

if st.button('Run'):
  for i in metrics:
    descriptive_metric.append(data.groupby('group').agg({i: ['mean', 'std']}))
  descriptive_metric = pd.concat(descriptive_metric, axis=1)
  descriptive_metric
  for metric in metrics:
    data_metrics = descriptive_metric[metric]
    na, nb = number_user.user_id
    ma, mb = data_metrics['mean']
    sa, sb = data_metrics['std']
    globals()[metric] = bayes.gaussian_ab_test(m_a=ma, s_a=sa, n_a=na, m_b=mb, s_b=sb, n_b=nb)
# except:
#   pass
for x in range(st.session_state["choices_len"]):
  st.write(st.session_state["metric" + f"{x}"])


table = open("app/index.html").read().format(control=control, variation =variation, na=na, nb=nb)

for x in range(st.session_state["choices_len"]):
  metric = eval(st.session_state["metric" + f"{x}"])
  risk = float("{:0.2f}".format(metric['risk'][1]))
  value_a = float("{:0.2f}".format(metric['mean']['m_a']))
  value_b = float("{:0.2f}".format(metric['mean']['m_b']))
  risk_percent = "{0:.2%}".format(risk / value_b)
  total_a = "{:0.2f}".format(na * value_a)
  total_b = "{:0.2f}".format(nb * value_b)
  chance_to_beat = "{0:.2%}".format(metric['chance_to_win'])
  percent_change = "{0:.2%}".format(metric['expected'])

  duration_metric = ""
  count_metric = ""
  binomial_metric = ""

  if st.session_state["type" + f"{x}"] == 'Duration':
    du_me = open("app/duration_metric.html").read()\
            .format(metric= st.session_state["metric" + f"{x}"]
            , risk_percent =risk_percent
            , risk = risk  , value_a = value_a, total_a = total_a, na = na
            ,value_b = value_b, total_b=total_b, nb=nb, chance_to_beat=chance_to_beat
            ,percent_change= percent_change
            )
    
    duration_metric = duration_metric + du_me

  elif st.session_state["type" + f"{x}"] == 'Count':
    count_me = open("app/count_metric.html").read()\
            .format(metric= st.session_state["metric" + f"{x}"]
            , risk_percent =risk_percent
            , risk = risk  , value_a = value_a, total_a = total_a, na = na
            ,value_b = value_b, total_b=total_b, nb=nb, chance_to_beat=chance_to_beat
            ,percent_change= percent_change
            )
    count_metric = count_metric + count_me
  elif st.session_state["type" + f"{x}"] == 'Binomial':
    bin_me = open("app/binomial_metric.html").read()\
            .format(metric= st.session_state["metric" + f"{x}"]
            , risk_percent =risk_percent
            , risk = risk  , value_a = value_a, total_a = total_a, na = na
            ,value_b = value_b, total_b=total_b, nb=nb, chance_to_beat=chance_to_beat
            ,percent_change= percent_change
            )
    binomial_metric = binomial_metric + bin_me

html_code = table + duration_metric + count_metric + binomial_metric

st.components.v1.html(html_code, height= 1000, scrolling=True)