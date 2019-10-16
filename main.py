import os, os.path
import pandas as pd
import cherrypy
import pydgraph
import json
from pandas.io.json import json_normalize

cherrypy.config.update("server.conf")

def query_data(client, queryStatement, queryName):

    query = queryStatement
    res = client.txn(read_only=True).query(query)
    return json.loads(res.json.decode('utf-8'))[queryName]

def main(queryStatement, host, queryName):
    client_stub = pydgraph.DgraphClientStub(host)
    client = pydgraph.DgraphClient(client_stub)
    result = query_data(client, queryStatement, queryName)
    client_stub.close()
    return result

paging_bucket = 2

def next_preview_buttons(page, data_frame):
   #get number of rows of dataframe
   nrows = data_frame.shape[0]
   if nrows <= paging_bucket:
       return ""
   if nrows%paging_bucket == 0:
     page_number = nrows//paging_bucket
   else:
     page_number = nrows//paging_bucket +1

   table_pagination = '<div id="table-pagination">\n'
   container_end = '</div>'

   #if first page then deactivate previews and first button
   if page == 1:
     table_pagination += """<button id="button-first" type="button" disabled>&laquo; First</button>
<button id="button-previous" type="button" disabled>&#8249; Previous</button>
<button id="button-next" type="button">Next &#8250;</button>
<button id="button-last" type="button">Last &raquo; </button>"""

   #if last page then deactivate next and last button
   elif page == page_number:
     table_pagination += """<button id="button-first" type="button" onclick="paging()">&laquo; First</button>
<button id="button-previous" type="button">&#8249; Previous</button>
<button id="button-next" type="button" disabled>Next &#8250;</button>
<button id="button-last" type="button" disabled>Last &raquo;</button>"""

   else:
     table_pagination += """<button id="button-first" type="button">&laquo; First</button>
<button id="button-previous" type="button">&#8249; Previous</button>
<button id="button-next" type="button">Next &#8250;</button>
<button id="button-last" type="button">Last &raquo;</button>"""

   return table_pagination + "\n" + container_end


#function returning the number of the lower row, hifher row and page number
#after clicking first, previous, next or last button
def paging_range(actual_page, action, data_frame):
    new_page,nrows =  cherrypy.session['queryResultDataFramePage'], data_frame.shape[0]
    if nrows%paging_bucket == 0:
      page_number = nrows//paging_bucket
    else:
      page_number = nrows//paging_bucket +1
    #no action (when query, filter and group)
    if action == "no-action":
      if nrows  <= paging_bucket:
        lower_row, higher_row, new_page = 0, nrows, 1
      else:
        lower_row, higher_row, new_page = 0, paging_bucket, 1
    #NEXT button
    elif action == "button-next":
      lower_row  = paging_bucket * actual_page
      #next page is last page and last page has different number of rows
      if actual_page + 1 == page_number and nrows%paging_bucket !=0:
        higher_row = nrows - lower_row + 1
      #if next page not last page
      else:
        higher_row = paging_bucket * (actual_page +1)
      new_page += 1

    #PREVIOUS button
    elif action == "button-previous":
      lower_row  = paging_bucket * (actual_page -2)
      higher_row = paging_bucket * (actual_page -1)
      new_page -= 1

    #LAST button
    elif action == "button-last":
      lower_row  = paging_bucket * (page_number -1)
      higher_row = nrows
      new_page= page_number

    #FIRST button
    elif action == "button-first":
      lower_row  = 0
      higher_row = paging_bucket
      new_page = 1
    return lower_row, higher_row, nrows, new_page

class tableApp(object):

    @cherrypy.expose
    def index(self):
        return open('index.html')

    @cherrypy.expose
    def query(self, *args, **kwargs):
        queryStatement = kwargs["query"][kwargs["query"].find("{")+1:kwargs["query"].find("(")].replace("\n", "").replace(" ", "")
        host = cherrypy.request.app.config['graphdb']['host']
        schema = main('schema{predicate type}', host, 'schema')
        print(schema)
        queryResult = main(kwargs["query"], host, queryStatement)
        print(queryResult)
        cherrypy.session['queryResultDataFrame'] = pd.DataFrame(queryResult)
        #cherrypy.session['queryResultDataFrame'] = pd.read_csv("http://data.insideairbnb.com/germany/be/berlin/2019-07-11/data/listings.csv.gz")
        print(cherrypy.session['queryResultDataFrame'].dtypes)
        cherrypy.session['queryResultDataFramePage'] = 1
        cherrypy.session['filter-parameter'], cherrypy.session['group-parameter'] =  '',''
        low_row, high_row, nrows, new_page = paging_range(cherrypy.session['queryResultDataFramePage'],"no-action", cherrypy.session['queryResultDataFrame'])
        range_info = '<p>Rows showed: ' + str(low_row+1) + '-' + str(high_row)  + ' / Total Rows: ' + str(nrows) + ' </p>'
        return range_info + next_preview_buttons(1, cherrypy.session['queryResultDataFrame']) + cherrypy.session['queryResultDataFrame'][low_row:high_row].to_html(na_rep="", border=0, index=False)

    @cherrypy.expose
    def filter_group(self, *args, **kwargs):
        cherrypy.session['queryResultDataFramePage'] = 1
        if kwargs['filter'] == "" and kwargs['group'] == '':
            cherrypy.session['filterGroupDataFrame'] = ''
            cherrypy.session['filter-parameter'], cherrypy.session['group-parameter'] =  '',''
            low_row, high_row, nrows, new_page = paging_range(cherrypy.session['queryResultDataFramePage'],"no-action", cherrypy.session['queryResultDataFrame'])
            range_info = '<p>Rows showed: ' + str(low_row+1) + '-' + str(high_row)  + ' / Total Rows: ' + str(nrows) + ' </p>'
            return range_info + next_preview_buttons(1, cherrypy.session['queryResultDataFrame']) + cherrypy.session['queryResultDataFrame'][low_row:high_row].to_html(na_rep="", border=0, index=False)
        elif kwargs['filter'] != "" and kwargs['group'] != '':
            cherrypy.session['filter-parameter'], cherrypy.session['group-parameter'] = kwargs['filter'], kwargs['group']
            #data frame with the group and filter parameter
            cherrypy.session['filterGroupDataFrame'] = cherrypy.session['queryResultDataFrame'].query(kwargs["filter"]).set_index(kwargs["group"].replace(' ', '').split(","))
            print(cherrypy.session['filterGroupDataFrame'])
            low_row, high_row, nrows, new_page = paging_range(cherrypy.session['queryResultDataFramePage'],"no-action", cherrypy.session['filterGroupDataFrame'])
            range_info = '<p>Rows showed: ' + str(low_row+1) + '-' + str(high_row)  + ' / Total Rows: ' + str(nrows) + ' </p>'
            return range_info + next_preview_buttons(1, cherrypy.session['filterGroupDataFrame']) + cherrypy.session['filterGroupDataFrame'][low_row:high_row].to_html(na_rep="", border=0)

        elif kwargs['filter'] == "": #only group parameter
            cherrypy.session['filter-parameter'], cherrypy.session['group-parameter'] = "",kwargs['group']
            #data frame with the filter parameter
            cherrypy.session['filterGroupDataFrame'] = cherrypy.session['queryResultDataFrame'].set_index(kwargs["group"].replace(' ', '').split(","))
            print(cherrypy.session['filterGroupDataFrame'])
            low_row, high_row, nrows, new_page = paging_range(cherrypy.session['queryResultDataFramePage'],"no-action", cherrypy.session['filterGroupDataFrame'])
            range_info = '<p>Rows showed: ' + str(low_row+1) + '-' + str(high_row)  + ' / Total Rows: ' + str(nrows) + ' </p>'
            return range_info + next_preview_buttons(1, cherrypy.session['filterGroupDataFrame']) + cherrypy.session['filterGroupDataFrame'][low_row:high_row].to_html(na_rep="", border=0)

        else: #only filter parameter
            cherrypy.session['filter-parameter'], cherrypy.session['group-parameter'] = kwargs['filter'], ""
            #data frame with the group parameter
            cherrypy.session['filterGroupDataFrame'] = cherrypy.session['queryResultDataFrame'].query(kwargs["filter"])
            print(cherrypy.session['filterGroupDataFrame'])
            low_row, high_row, nrows, new_page = paging_range(cherrypy.session['queryResultDataFramePage'],"no-action", cherrypy.session['filterGroupDataFrame'])
            range_info = '<p>Rows showed: ' + str(low_row+1) + '-' + str(high_row)  + ' / Total Rows: ' + str(nrows) + ' </p>'
            return range_info + next_preview_buttons(1, cherrypy.session['filterGroupDataFrame']) + cherrypy.session['filterGroupDataFrame'][low_row:high_row].to_html(na_rep="", border=0, index=False)

    @cherrypy.expose
    def paging(self, *args, **kwargs):
        print(cherrypy.session['filter-parameter'], cherrypy.session['group-parameter'])
        dataFramePaging = cherrypy.session['queryResultDataFrame'] if cherrypy.session['filter-parameter'] == "" and cherrypy.session['group-parameter'] == "" else cherrypy.session['filterGroupDataFrame']
        print(dataFramePaging)
        low_row, high_row, nrows, new_page = paging_range(cherrypy.session['queryResultDataFramePage'],kwargs['button'], dataFramePaging)
        cherrypy.session['queryResultDataFramePage'] = new_page
        range_info = '<p>Rows showed: ' + str(low_row+1) + '-' + str(high_row)  + ' / Total Rows: ' + str(nrows) + ' </p>'
        return range_info + next_preview_buttons(new_page, dataFramePaging) + dataFramePaging[low_row:high_row].to_html(na_rep="", border=0, index=False if cherrypy.session['filter-parameter'] == "" and cherrypy.session['group-parameter'] == "" else True)

if __name__ == '__main__':
    cherrypy.quickstart(tableApp(), '/', "server.conf")
