# Copyright (C) 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Service details and instances for the Finance service.

Some use cases:
Create portfolio:
  finance create --title "Some Portfolio" --currency USD

Delete portfolio:
  finance delete --title "Some Portfolio"

List portfolios:
  finance list

Create position:
  finance create-pos --title "Some Portfolio" --ticker NYSE:PCLN

Delete position:
  finance delete-pos --title "Some Portfolio" --ticker NYSE:PCLN

List positions:
  finance list-pos --title "Some Portfolio"

Create transaction:
  finance create-txn --title "Some Portfolio" --ticker NASDAQ:PCLN
          --currency USD --ttype Sell --price 346.60 --commission 7.7
          --shares 60 --date 2010-09-24 --notes "Stop loss on 347.01"

Delete transaction:
  finance delete-txn --title "Some Portfolio"
                             --ticker NASDAQ:PCLN --txnid 4

List transactions:
  finance list-txn --title "Some Portfolio" --ticker NASDAQ:PCLN

"""

__author__ = 'bartosh@gmail.com (Ed Bartosh)'

import sys
import os
import inspect
import logging
import datetime

import googlecl
import googlecl.calendar.date
from googlecl.base import BaseCL, Task
from googlecl.service import BaseServiceCL
from googlecl.finance import SECTION_HEADER

from gdata.service import RequestError
from gdata.finance.service import FinanceService, PortfolioQuery, PositionQuery
from gdata.finance import PortfolioData, PortfolioEntry, TransactionEntry, \
                          TransactionData, Money, Price, Commission, \
                          PortfolioFeedFromString

LOG = logging.getLogger(googlecl.finance.LOGGER_NAME)

class FinanceServiceCL(FinanceService, BaseServiceCL):

  """Extends gdata.photos.service.FinanceService for the command line.

  This class adds some features focused on using Finance via an installed app
  with a command line interface.

  """

  def __init__(self):
    """Constructor."""
    FinanceService.__init__(self)
    BaseServiceCL.__init__(self, SECTION_HEADER)
    self.max_results = None

  def is_token_valid(self, test_uri='/data/feed/api/user/default'):
    """Check that the token being used is valid."""
    return BaseCL.IsTokenValid(self, test_uri)

  IsTokenValid = is_token_valid

  def get_portfolio_entries(self, title=None, returns=False, positions=False,
                            multiple=True):
    """Get portfolio entries or one entry.
    Args:
      title: string, portfolio title, could be regexp.
      returns: [optional] boolean, include returns into the result.
      positions: [optional] boolean, include positions into the result.
      multiple: boolean, return multiple entries if True
    Returns: list of portfolio entries
    """

    query = PortfolioQuery()
    query.returns = returns
    query.positions = positions

    uri = "/finance/feeds/default/portfolios/" + query.ToUri()

    if multiple:
      return self.GetEntries(uri, titles=title,
                             converter=PortfolioFeedFromString)
    else:
      entry = self.GetSingleEntry(uri, title=title,
                                  converter=PortfolioFeedFromString)
      if entry:
        return [entry]
      else:
        return []

  def get_portfolio(self, title, returns=False, positions=False):
    """Get portfolio by title.
    Args:
      title: string, portfolio title.
      returns: [optional] boolean, include returns into the result.
      positions: [optional] boolean, include positions into the result.

    Returns: portfolio feed object or None if not found.
    """

    entries = self.get_portfolio_entries(title=title, returns=returns,
                                     positions=positions, multiple=False)
    if entries:
      return entries[0]
    else:
      LOG.info('Portfolio "%s" not found' % title)
      return None

  def create_transaction(self, pfl, ttype, ticker, shares=None, price=None,
                         currency=None, commission=None, date='', notes=None):
    """Create transaction.

    Args:
      pfl: portfolio object.
      ttype: string, transaction type, on of the 'Buy', 'Sell',
             'Short Sell', 'Buy to Cover'.
      shares: [optional] decimal, amount of shares.
      price: [optional] decimal, price of the share.
      currency: [optional] string, portfolio currency by default.
      commission: [optional] decimal, brocker commission.
      date: [optional] string, transaction date,
            datetime.now() by default.
      notes: [optional] string, notes.

    Returns:
      None if transaction created successfully, otherwise error string.
    """
    if not currency:
      currency = pfl.portfolio_data.currency_code
    if date is None:
      # if date is not provided from the command line current date is set
      date = datetime.datetime.now().isoformat()
    elif date is '':
      # special case for create position task. date should be set to None
      # to create empty transaction. See detailed explanations in
      # the _run_create_position function below
      date = None
    else:
      parser = googlecl.calendar.date.DateParser()
      date = parser.parse(date).local.isoformat()

    if price is not None:
      price = Price(money=[Money(amount=price, currency_code=currency)])
    if commission is not None:
      commission = Commission(money=[Money(amount=commission,
                                             currency_code=currency)])
    txn = TransactionEntry(transaction_data=TransactionData(
        type=ttype, price=price, shares=shares, commission=commission,
        date=date, notes=notes))

    try:
      self.AddTransaction(txn, portfolio_id=pfl.portfolio_id,
                          ticker_id=ticker)
    except RequestError, err:
      return err[0]['body']


SERVICE_CLASS = FinanceServiceCL

class BaseFormatter(object):
  """Base class for formatters."""

  def __init__(self, avail_fields, fields, sep=','):
    """Init formatter
    Args:
      avail_fields: list of tuples [(field_name, format_spec), ...] for all
                    possible fields
      fields: string, list of <sep>-separated requested fields names.
      sep: string, separator, comma by default
    """
    if fields:
      self.fields = fields.split(sep)
    else:
      self.fields = [item[0] for item in avail_fields]

    self.avail_fields = avail_fields
    avail_dict = dict(avail_fields)
    self.format = ' '.join(avail_dict[name] for name in self.fields)

  @property
  def header(self):
    """Make output header.
    Uses names of available fields as column headers. replaces
    '_' with ' ' and capitalizes them. Utilizes the same format as
    used for body lines: self.format

    Returns: string, header.
    """
    return self.format % \
        dict([(item[0], item[0].replace('_', ' ').capitalize()) \
                for item in self.avail_fields])

  def get_line(self, entry):
    """Get formatted entry. Abstract method.
    Args:
      entry: entry object
    Returns:
      string, formatted entry.
    """
    raise NotImplementedError("Abstract method %s.%s called" % \
                                (self.__class__.__name__,
                                 inspect.stack()[0][3] ))

  def output(self, entries, stream=sys.stdout):
    """Output list of entries to the output stream.

    Args:
      entries: list of entries.
      stream: output stream.
    """

    if self.header:
      stream.write(self.header + os.linesep)
    for entry in entries:
      stream.write(self.get_line(entry) + os.linesep)

class PortfolioFormatter(BaseFormatter):
  avail_fields = [('id', '%(id)3s'), ('title', '%(title)-15s'),
                  ('curr', '%(curr)-4s'),
                  ('gain', '%(gain)-10s'),
                  ('gain_persent', '%(gain_persent)-14s'),
                  ('cost_basis', '%(cost_basis)-10s'),
                  ('days_gain', '%(days_gain)-10s'),
                  ('market_value', '%(market_value)-10s')]

  def __init__(self, fields):
    super(self.__class__, self).__init__(self.avail_fields, fields)

  def get_line(self, entry):
    data =  entry.portfolio_data
    return self.format % \
      {'id': entry.portfolio_id, 'title': entry.portfolio_title,
       'curr': data.currency_code,
       'gain': data.gain and data.gain.money[0].amount,
       'gain_persent': '%-14.2f' % (float(data.gain_percentage) * 100,),
       'cost_basis': data.cost_basis and data.cost_basis.money[0].amount,
       'days_gain': data.days_gain and data.days_gain.money[0].amount,
       'market_value': data.market_value and data.market_value.money[0].amount
      }

class PositionFormatter(BaseFormatter):
  avail_fields = [('ticker', '%(ticker)-14s'), ('shares', '%(shares)-10s'),
                  ('gain', '%(gain)-10s'),
                  ('gain_persent', '%(gain_persent)-14s'),
                  ('cost_basis', '%(cost_basis)-10s'),
                  ('days_gain', '%(days_gain)-10s'),
                  ('market_value', '%(market_value)-10s')]

  def __init__(self, fields):
    super(self.__class__, self).__init__(self.avail_fields, fields)

  def get_line(self, entry):
    data =  entry.position_data
    return self.format % \
      {'ticker': entry.ticker_id, 'shares': data.shares,
       'gain': data.gain and data.gain.money[0].amount,
       'gain_persent': '%-14.2f' % (float(data.gain_percentage) * 100,),
       'cost_basis': data.cost_basis and data.cost_basis.money[0].amount,
       'days_gain': data.days_gain and data.days_gain.money[0].amount,
       'market_value': data.market_value and data.market_value.money[0].amount
      }

class TransactionFormatter(BaseFormatter):
  avail_fields = [('id', '%(id)-3s'), ('type', '%(type)-12s'),
                  ('shares', '%(shares)-10s'), ('price', '%(price)-10s'),
                  ('commission', '%(commission)-10s'),
                  ('date', '%(date)-10s'), ('notes', '%(notes)-30s')]

  def __init__(self, fields):
    super(self.__class__, self).__init__(self.avail_fields, fields)

  def get_line(self, entry):
    data =  entry.transaction_data
    if data.date:
      data.date = data.date[:10] # stip isoformat tail
    return self.format % \
      {'id': entry.transaction_id, 'type': data.type, 'shares': data.shares,
       'price': data.price.money[0].amount,
       'commission': data.commission.money[0].amount,
       'date': data.date or '', 'notes': data.notes or ''}

#===============================================================================
# Each of the following _run_* functions execute a particular task.
#
# Keyword arguments:
#  client: Client to the service being used.
#  options: Contains all attributes required to perform the task
#  args: Additional arguments passed in on the command line, may or may not be
#        required
#===============================================================================

# Portfolio-related tasks
def _run_create(client, options, args):
  pfl = PortfolioEntry(
    portfolio_data=PortfolioData(currency_code=options.currency))
  pfl.portfolio_title = options.title
  try:
    client.AddPortfolio(pfl)
  except RequestError, err:
    LOG.error('Failed to create portfolio: %s' % err[0]['body'])

def _run_delete(client, options, args):
  entries = client.get_portfolio_entries(options.title, positions=True)
  if entries:
    client.DeleteEntryList(entries, 'portfolio', True)

def _run_list(client, options, args):
  entries = client.get_portfolio_entries(returns=True)
  if entries:
    PortfolioFormatter(options.fields).output(entries)
  else:
    LOG.info('No portfolios found')

# Position-related tasks
def _run_create_position(client, options, args):
  # Quote from Developer's Guide:
  #   You can't directly create, update, or delete position entries;
  #   positions are derived from transactions.
  #   Therefore, to create or modify a position, send appropriate
  #   transactions on that position.
  pfl = client.get_portfolio(options.title, positions=True)
  if pfl:
    # create empty transaction
    err = client.create_transaction(pfl, "Buy", options.ticker)
    if err:
      LOG.error("Failed to create position: %s" % err)

def _run_delete_positions(client, options, args):
  pfl = client.get_portfolio(options.title, positions=True)
  if pfl:
    if not pfl.positions:
      LOG.info('No positions found in this portfolio')
    else:
      try:
        if options.ticker:
          positions = [client.GetPosition(portfolio_id=pfl.portfolio_id,
                                          ticker_id=options.ticker,
                                          query=PositionQuery())]
        else:
          positions = client.GetPositionFeed(portfolio_entry=pfl).entry

        client.DeleteEntryList(positions, 'position', True,
                 callback=lambda pos: client.DeletePosition(position_entry=pos))
      except RequestError, err:
        LOG.error("Failed to delete position: %s" % err[0]['body'])

def _run_list_positions(client, options, args):
  pfl = client.get_portfolio(options.title, returns=True, positions=True)
  if pfl:
    if pfl.positions:
      PositionFormatter(options.fields).output(pfl.positions)
    else:
      LOG.info('No positions found in this portfolio')

# Transaction-related tasks
def _run_create_transaction(client,  options, args):
  pfl = client.get_portfolio(options.title)
  if pfl:
    err = client.create_transaction(pfl, options.ttype, options.ticker,
                                      options.shares, options.price,
                                      options.currency, options.commission,
                                      options.date, options.notes)
    if err:
      LOG.error("Failed to create transaction: %s" % err)

def _run_delete_transactions(client,  options, args):
  pfl = client.get_portfolio(options.title)
  if pfl:
    try:
      if options.txnid:
        transactions = [client.GetTransaction(portfolio_id=pfl.portfolio_id,
                                              ticker_id=options.ticker,
                                              transaction_id=options.txnid)]
      else:
        transactions = client.GetTransactionFeed(portfolio_id=pfl.portfolio_id,
                                                 ticker_id=options.ticker).entry
      client.DeleteEntryList(transactions, 'transaction', True)
    except RequestError, err:
      LOG.error("Failed to delete transaction[s]: %s" % err[0]['body'])

def _run_list_transactions(client,  options,  args):
  pfl = client.get_portfolio(options.title)
  if pfl:
    try:
      transactions = client.GetTransactionFeed(
        portfolio_id=pfl.portfolio_id,
        ticker_id=options.ticker).entry
    except RequestError, err:
      LOG.error("Failed to get transactions: %s" % err[0]['body'])
    else:
      TransactionFormatter(options.fields).output(transactions)

TASKS = {'create': Task('Create a portfolio',
                        callback=_run_create,
                        required=['title', 'currency']),
         'delete': Task('Delete portfolios',
                        callback=_run_delete,
                        required = 'title'),
         'list':   Task('List portfolios',
                        callback=_run_list,
                        optional=['fields']),
         'create-pos': Task('Create position',
                            callback=_run_create_position,
                            required = ['title', 'ticker']),
         'delete-pos': Task('Delete positions',
                            callback=_run_delete_positions,
                            required = ['title'],
                            optional = ['ticker']),
         'list-pos':  Task('List positions',
                           callback=_run_list_positions,
                           required = 'title'),
         'create-txn': Task('Create transaction',
                            callback=_run_create_transaction,
                            required = ['title', 'ticker', 'ttype'],
                            optional = ['shares', 'price', 'date',
                                 'commission', 'currency', 'notes']),
         'list-txn': Task('List transactions',
                          callback=_run_list_transactions,
                          required = ['title', 'ticker']),
         'delete-txn': Task('Delete transactions',
                            callback=_run_delete_transactions,
                            required = ['title', 'ticker'],
                            optional=['txnid']),
}

# Local Variables:
# mode: python
# py-indent-offset: 2
# indent-tabs-mode: nil
# tab-width: 2
# End:
