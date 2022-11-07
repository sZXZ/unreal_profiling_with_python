from datetime import datetime
import pandas as pd
import re


def build_hierarchy(object, space_count):
    time_str = datetime.now().strftime('%H%M%S')
    values = f"var object_{time_str} = {object}; var space_{time_str} = {space_count}; const htmlgraphicsValue_{time_str} = document.getElementById('htmlgraphics-value_{time_str}');"
    javascript = """function refresh_INDICATOR(){htmlNode_INDICATOR=document;function s(s,e){if(object_INDICATOR[e].includes("FRAME")||object_INDICATOR[e].includes("Culled to"))return-1;check_arr=s.slice().reverse().slice(-1*e);for(var r=0;r<check_arr.length;r++)if(check_arr[r]<s[e])return check_arr.length-r-1;return 0}parent_index_INDICATOR=[];for(var e=0;e<space_INDICATOR.length;e++)parent_index_INDICATOR.push(s(space_INDICATOR,e));function r(s,e){children=[];for(var r=0;r<s.length;r++)s[r]!=e||visited[r]||(children.push(r),visited[r]=!0);return children}string_INDICATOR="",prefix='<span style="visibility: hidden">',postfix="</span>",obj_INDICATOR={},visited=Array(parent_index_INDICATOR.length).fill(!1),htmlgraphicsValue_INDICATOR.innerHTML="";for(var t=0;t<object_INDICATOR.length;t++){null==htmlNode_INDICATOR.getElementById("id_INDICATOR_"+t)&&(htmlgraphicsValue_INDICATOR.innerHTML+='<ul id="id_INDICATOR_'+t+'" style="list-style-type: disclosure-closed;"><li>'+object_INDICATOR[t]+"</li></ul>"),display=r(parent_index_INDICATOR,t);for(var i=0;i<display.length;i++)display[i]!=t&&(htmlNode_INDICATOR.getElementById("id_INDICATOR_"+t).innerHTML+='<ul id="id_INDICATOR_'+display[i]+'" style="display: none;list-style-type: disclosure-closed;"><li>'+object_INDICATOR[display[i]]+"</li></ul>")}for(t=0;t<object_INDICATOR.length;t++)htmlNode_INDICATOR.getElementById("id_INDICATOR_"+t).getElementsByTagName("li")[0].onclick=function(s){my_parent=this.parentElement,ul_tags=my_parent.getElementsByTagName("ul"),state=my_parent.style.listStyleType,hid=!1;for(var e=0;e<ul_tags.length;e++)(ul_tags[e].parentElement==my_parent||s.shiftKey)&&(vis=ul_tags[e].style.display,"disclosure-open"==state&&(hid=!0,s.shiftKey&&(ul_tags[e].style.listStyleType="disclosure-closed"),ul_tags[e].style.display="none"),"disclosure-closed"==state&&(hid=!1,s.shiftKey&&(ul_tags[e].style.listStyleType="disclosure-open"),ul_tags[e].style.display="block"));hid?my_parent.style.listStyleType="disclosure-closed":my_parent.style.listStyleType="disclosure-open"}}refresh_INDICATOR();"""
    style = """*{font-family:Roboto,Helvetica,Arial,sans-serif}.box{border:solid #555 2px;border-radius:10px;padding:10px 20px;}"""
    html = f"""<style>{style}</style><div><div class="box" id="htmlgraphics-value_{time_str}"></div></div><script>{values}{javascript.replace('INDICATOR', time_str)}</script>"""
    return html

def parse_profile_gpu(row):
    percentage, data = row['lines'].split('%')
    data = data.split()
    row['ms'] = float(data[0][:-2])
    row['name'] = data[1]
    values_to_parse = {
        'draws':['draw'],
        'prims':['prim'], 
        'verts':['vert'], 
        'dispatches':['dispatch'], 
        'groups':['group']
    }
    for val in values_to_parse:
        row[val] = data[data.index(val)-1] if val in data else '0'
        for alt_name in values_to_parse[val]:
            row[val] = data[data.index(alt_name)-1] if alt_name in data else row[val]
        if 'x' in row[val]:
            row[val] = row[val].split('x')
    return row

def profile_gpu(log):
    lines = []
    spaces = []
    values = []
    is_profilegpu = False
    for line in log:
        if 'LogRHI' in line:
            clean_line = re.sub(r'\[.{24}\[...]\w+: ', '', line)
            if 'FRAME' in line:
                is_profilegpu = True
            if 'Total Nodes' in line:
                is_profilegpu = False
            if is_profilegpu:
                value = float(clean_line.split()[0].split('%')[0])
                values.append(value)
                lines.append(clean_line)
                add = 0
                if value > 10.0 and not 'FRAME' in line:
                    add = 1
                spaces.append(len(clean_line) - len(clean_line.lstrip()) + add)
    df = pd.DataFrame({"lines": lines, "spaces": spaces, "values": values})
    df = df.apply(parse_profile_gpu, axis=1)
    return build_hierarchy(df['lines'].to_list(), df['spaces'].to_list()), df


def profile_cpu(log):
    lines = []
    spaces = []
    values = []
    is_profile = False
    for line in log:
        if 'LogStats' in line:
            add = 0
            clean_line = re.sub(r'\[.{24}\[...]\w+: ', '', line)
            if 'Culled to' in line:
                add = -100
                is_profile = True
            if is_profile:
                value = 0
                try:
                    value = float(clean_line.split()[0].split('ms')[0])
                except:
                    pass
                if value > 10.0 and not 'Culled to' in line:
                    add = 1
                values.append(value)
                spaces.append(len(clean_line) -
                              len(clean_line.lstrip()) + add)
                lines.append(clean_line)
    df = pd.DataFrame({"lines": lines, "spaces": spaces, "values": values})
    return build_hierarchy(df['lines'].to_list(), df['spaces'].to_list())
