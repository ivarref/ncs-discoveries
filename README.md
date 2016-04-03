Ncs-discoveries
===============

When was the petroleum on the Norwegian Continental Shelf discovered?

[View page](http://ivarref.github.io/ncs-discoveries/).

Notes about the data
--------------------

_PDO_ is an abbrevation for Plan for Development and Operation.

_Remaining reserves_ refers to recoverable reserves in active, producing fields.

_All petroleum_ includes oil, condensate, gas and NGL.

Discoveries that are not evaluated and where development is not very likely is not included in the diagram.

Update
------

    git clone git@github.com:ivarref/ncs-discoveries.git && \
    cd ncs-discoveries && ./pull_data.py && \
    git commit -am "$(date): update data" && git push && \
    git checkout gh-pages && git merge master && git push

Comments
--------
refsdal.ivar@gmail.com

