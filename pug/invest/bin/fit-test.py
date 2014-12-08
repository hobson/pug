from statsmodels.tsa import arima_model
import numpy as np
from pug.invest import util

y = util.simulate(poly=100, sinusoids=(10, 100, -20)).values

hr = np.arange(365*96)*.25
sinusoids = [
    np.random.normal(0.0, 0.1, 365*96)+10 + 3*np.sin(hr*2*np.pi/96/.25),
    np.random.normal(0.0, 0.1, 365*96)+15 + 3*np.sin(hr*2*np.pi/96/.25) + 3*np.cos(t*2*np.pi/96./.25/365.),
    np.random.normal(0.0, 1.0, 365*96)+15 + 3*np.sin(hr*2*np.pi/96/.25) + 3*np.cos(t*2*np.pi/96./.25/365.)+np.random.normal(0.0,1e-5,365*96).cumsum()]
arma20 = arima_model.ARMA(y, (2,0)).fit()
y2 = arma.predict(start=10*96, end=12*96)
y1 = y[10*96-1:12*96]
plt.plot(t[10*96-1:12*96],zip(*[y1,y2]))
plt.show()
y2 = arma30.predict(start=10*96, end=12*96)
plt.plot(t[10*96-1:12*96],zip(*[y1,y2]))
plt.show()
arma30.resid.plot()
plt.plot(arma30.resid)
plt.show()
plt.plot(arma30.resid/y2)
plt.plot(arma30.resid/y)
plt.show()
plt.plot(arma30.resid/y)
plt.show()
arima_model.ARMA??
arima_model.ARMA?
arma30.predict??
arma30.predict?
arma30 = arima_model.ARMA(y[:-96*30], (2,0)).fit()
y1 = y[-32*96:]
y2 = arma30.predict(start=N-32*96, end=N-28*96)
N=len(y)
y2 = arma30.predict(start=N-32*96, end=N-28*96)
plt.plot(t[-32*96-1:-28*96],zip(*[y1,y2]))
plt.show()
plt.plot(t[-32*96-1:-28*96],zip(*[y1,y2]))
plt.show()
N
arma30 = arima_model.ARMA(y[:-96*30], (3,0)).fit()
N_predict=len(y[:-96*30])
y_predict=y[:-96*30]
y2 = arma30.predict(start=N_predict,end=N_predict+96)
y1 = y[N_predict:N_predict+96]
y1-y2
y2 = arma30.predict(start=N_predict,end=N_predict+95)
plt.plot(zip(*[y1,y2]))
plt.plot(zip(*[y1,y2]))
plt.show()
arma41 = arima_model.ARMA(y_train, (4,1)).fit()
y_train=y[:-96*30]
arma41 = arima_model.ARMA(y_train, (4,1)).fit()

arma296 = arima_model.ARMA(y_train, (2,96)).fit()
arma296 = arima_model.ARMA(y_train.diff(), (2,96)).fit()
arma296 = arima_model.ARMA(pd.Series(y_train).diff(), (2,96)).fit()
import pandas as pd
y_diff = pd.Series(y).diff().values()
y_diff = pd.Series(y).diff().values
y_train=y_diff[:-96*30]
arma296 = arima_model.ARMA(y_train, (2,96)).fit()
arma296 = arima_model.ARMA(y_train, (2,0)).fit()
arma296 = arima_model.ARMA(y_train[1:], (2,0)).fit()
arma296 = arima_model.ARMA(y_train[-96*14:], (2,96)).fit()
arma296 = arima_model.ARMA(y_train[-96*7:], (2,96)).fit()
arma296 = arima_model.ARMA(y_train[-96*2:], (2,96)).fit()
arma296 = arima_model.ARMA(y_train[-96*3:], (2,96)).fit()
arma296 = arima_model.ARMA(y_train[-96*4:], (2,96)).fit()
arma296 = arima_model.ARMA(y_train[-96*14:], (2,48)).fit()
arma296 = arima_model.ARMA(y_train[-96*14:], (2,24)).fit()
arma296 = arima_model.ARMA(y_train[-96*14:], (0,96)).fit()
arma296 = arima_model.ARMA(y_train[-96*14:], (1,96)).fit()
arma296 = arima_model.ARMA(y_train[-96*14:], (1,96)).fit(meth='mle')
arma296 = arima_model.ARMA(y_train[-96*14:], (1,96)).fit(meth='css')
arma296 = arima_model.ARMA(np.diff(y_train[-96*14:]).dropna(), (1,96)).fit(meth='css')
arma296 = arima_model.ARMA(np.diff(y_train[-96*14:])[1:], (2,96)).fit(meth='css')
arma296 = arima_model.ARMA(np.diff(y_train[-96*14:])[1:], (2,96)).fit(meth='mle')
arma296 = arima_model.ARMA(np.diff(y_train[-96*14:])[1:], (2,96)).fit?
arma296 = arima_model.ARMA(np.diff(y_train[-96*14:])[1:], (2,96))
arma296.fit?
arma296.fit(trend='c',solver='bfgs')
arma296.fit?
arma296.fit(trend='c',solver='bfgs',transparams=True)
arma296.fit?
arma296.fit(trend='c',solver='bfgs',transparams=False)
arma296.fit?
arma296._fit_start_params
arma296._fit_start_params()
arma296.fit?
arma296._fit_start_params?
arma296._fit_start_params??
arma296.fit(meth='css-mle',trend='c',solver='bfgs',transparams=False)
arma296.fit(meth='css-mle',trend='c',solver='bfgs',transparams=True)
q = np.zeros(96)
q[0] = 1
q[-1]=1
q[-1]=.5
q[0] = .1
q[-1]=.9
p=[10, 1.2, -.2]
arma296.fit(meth='css-mle',trend='c',solver='bfgs',transparams=True,startparams=[p,q])
arma296.fit?
arma296.fit?
arma296.fit(meth='css-mle',trend='c',solver='bfgs',transparams=True,start_params=[p,q])
np.log
arma296.fit(meth='css-mle',trend='c',solver='bfgs',transparams=False,start_params=[p,q])
p=np.array([10, 1.2, -.2])
arma296.fit(meth='css-mle',trend='c',solver='bfgs',transparams=False,start_params=[p,q])
arma296.fit(meth='css-mle',trend='c',solver='bfgs',transparams=False,start_params=np.array([p,q]))
arma296.fit(meth='css-mle',trend='c',solver='bfgs',transparams=False,start_params=q)
q.shape
q = np.zeros(93)
q[-1]=.9
q[0]=.1
arma296.fit(meth='css-mle',trend='c',solver='bfgs',transparams=False,start_params=q)
arma296.fit(trend='c',solver='bfgs',transparams=False,start_params=q)
arma296.fit(trend='c',transparams=False,start_params=q)
arma296.fit(transparams=False,start_params=q)
len(q)
p=np.array([10, 1.2, -.2])
q = np.zeros(99)
q[0]=.1
q[0]=10
q[1]=1
q[2]=-.2
q[-1]=.95
arma296.fit(transparams=False,start_params=q)

