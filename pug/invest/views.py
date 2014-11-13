# Create your views here.
import datetime
from django.views.generic import TemplateView
import sim
from pug.miner.views import d3_plot_context

class PlotSymbolView(TemplateView):
    """Query the miner.AggregateResults table to retrieve values for plotting in a bar chart"""
    template_name = 'miner/dashboard.d3.html'

    def get_context_data(self, context, **kwargs):
        # Call the base implementation first to get a context
        context = super(PlotSymbolView, self).get_context_data(**kwargs)
        symbols = sim.normalize_symbols(self.kwargs['symbols'])
        df = sim.price_dataframe(symbols=symbols,
            start=datetime.datetime(2010, 1, 1),
            end=datetime.datetime(2010, 3, 31),  
            price_type='close')
        context['df'] = df
        return d3_plot_context(context,
            table=df, title='Price History', xlabel='Date', ylabel='Adjusted Close', 
            header=['Date'] + df.columns)
