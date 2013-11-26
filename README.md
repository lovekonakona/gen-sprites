gen-sprite
==========

gen-sprite 是帮你将网站中使用的图片合并成一张图片并生成css的工具.

####准备工作

使用前请确保己安装python, imagemagick, 以及必要的python包yaml, jinja2, wand(建议使用pip安装)


####创建配置文件
配件文件是告诉脚本你要合并图片的规则. 配置文件使用yaml.
```yaml
  dir: . # dir 表示之后描述的文件相对于哪个目录, 若省略, 默认表示当前目录.
  imgs:  # imgs 表示要生成的图片, 使用list, 即可同时处理生成多张图片.
    - name: icons.png  # 多图合并功能使用(未来开放此功能)
      files: # files表示待合并的图片, 可以使用glob正则, 允许string(若只有一条规则)和list格式.
        - 'icons/icon*.png'
      output: output/icons.png # 表示输出文件位置, 若省略则和name同名, 生成在当前目录, 若不想输出内容, 请指定为false
      css: # 表示要生成的css文件, 若省略, 则不输出css文件
        template: icons.css.template # 表示要输出的css模版位置, 不填写则不输出内容
        output: output/icons.css # css输出的位置, 不填写则不输出内容
```

####创建css模版文件
css模版文件可以输出指定的css样式, 也可以输出less, sass或其他格式的内容, css模版只指基础的模版支持, 和语言无关.
模版文件使用jinja2(基于python的模版引擎)

模版文件中可使用的变量有

* canvas 表示画布信息
  
  可使用属性:

  width: 表示画布宽度

  height: 表示画布高度

* images 表示图片列表

  可使用属性:
  
  name: 表示图片的文件名(己去除扩展名).
  
  width: 表示图片宽度.
  
  height: 表示图片高度.
  
  background_position: 表示图片相对于合并后图片的位置.

```jinja
.icon {
    background-image: url(icon.png);
}

{% for img in images %}
.{{ img.name }} {
    background-position: {{ img.background_position }};
    width: {{ img.width }};
    height: {{ img.height }};
}
{% endfor %}
```
