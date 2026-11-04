/* WITH Dental site runtime: renders the page template with its logic class.
   Supports {{holes}}, <sc-for list as>, <sc-if value>, onX="{{fn}}" handlers.
   The page ships prerendered HTML; this script takes over and keeps it live. */
(function () {
  'use strict';

  function DCLogic(props) { this.props = props || {}; this.state = {}; }
  DCLogic.prototype.setState = function (patch) {
    var next = typeof patch === 'function' ? patch(this.state) : patch;
    this.state = Object.assign({}, this.state, next);
    if (this.__schedule) this.__schedule();
  };
  window.DCLogic = DCLogic;

  var HOLE = /\{\{\s*([^}]+?)\s*\}\}/g;
  var ONLY = /^\{\{\s*([^}]+?)\s*\}\}$/;
  var BOOL_ATTRS = { disabled: 1, checked: 1, hidden: 1, open: 1, selected: 1, readonly: 1, required: 1 };

  function lookup(path, scope) {
    if (path === 'true') return true;
    if (path === 'false') return false;
    var parts = path.split('.');
    var v = scope;
    for (var i = 0; i < parts.length; i++) {
      if (v == null) return undefined;
      v = v[parts[i]];
    }
    return v;
  }

  function interp(str, scope) {
    return str.replace(HOLE, function (_, p) {
      var v = lookup(p, scope);
      return v == null || v === false ? '' : String(v);
    });
  }

  function truthy(v) { return !!v && v !== 'false'; }

  function render(nodes, scope, out) {
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if (n.nodeType === 3) {
        out.push(document.createTextNode(n.data.indexOf('{{') >= 0 ? interp(n.data, scope) : n.data));
      } else if (n.nodeType === 1) {
        var tag = n.localName;
        if (tag === 'sc-for') {
          var list = lookup((n.getAttribute('list') || '').replace(/^\{\{\s*|\s*\}\}$/g, ''), scope) || [];
          var as = n.getAttribute('as') || 'item';
          for (var j = 0; j < list.length; j++) {
            var s = Object.create(scope);
            s[as] = list[j];
            render(n.childNodes, s, out);
          }
        } else if (tag === 'sc-if') {
          var cond = lookup((n.getAttribute('value') || '').replace(/^\{\{\s*|\s*\}\}$/g, ''), scope);
          if (truthy(cond)) render(n.childNodes, scope, out);
        } else {
          var el = n.cloneNode(false);
          var dyn = [];
          var handlers = null;
          var attrs = Array.prototype.slice.call(n.attributes);
          for (var a = 0; a < attrs.length; a++) {
            var name = attrs[a].name, val = attrs[a].value;
            if (name.indexOf('hint-') === 0) { el.removeAttribute(name); continue; }
            if (val.indexOf('{{') < 0) continue;
            var m = val.match(ONLY);
            if (/^on[a-z]/i.test(name)) {
              el.removeAttribute(name);
              var fn = m ? lookup(m[1], scope) : null;
              if (typeof fn === 'function') {
                handlers = handlers || {};
                handlers[name.slice(2).toLowerCase()] = fn;
              }
              continue;
            }
            dyn.push(name);
            if (m) {
              var v = lookup(m[1], scope);
              if (v == null || v === false || (BOOL_ATTRS[name] && v === 'false')) el.removeAttribute(name);
              else el.setAttribute(name, v === true ? (BOOL_ATTRS[name] ? '' : 'true') : String(v));
            } else {
              el.setAttribute(name, interp(val, scope));
            }
          }
          el.__wdDyn = dyn;
          el.__wdH = handlers;
          var kids = [];
          render(n.childNodes, scope, kids);
          for (var k = 0; k < kids.length; k++) el.appendChild(kids[k]);
          out.push(el);
        }
      }
    }
    return out;
  }

  // Attributes the visitor changes (an opened <details>) stay as they are unless the template binds them.
  var USER_STATE = { open: 1 };
  function patchAttrs(oldEl, newEl) {
    var dyn = newEl.__wdDyn || [];
    var i, a;
    var na = newEl.attributes;
    for (i = 0; i < na.length; i++) {
      a = na[i];
      if (USER_STATE[a.name] && dyn.indexOf(a.name) < 0) continue;
      if (oldEl.getAttribute(a.name) !== a.value) oldEl.setAttribute(a.name, a.value);
    }
    var oa = Array.prototype.slice.call(oldEl.attributes);
    for (i = 0; i < oa.length; i++) {
      a = oa[i];
      if (USER_STATE[a.name] && dyn.indexOf(a.name) < 0) continue;
      if (!newEl.hasAttribute(a.name)) oldEl.removeAttribute(a.name);
    }
    oldEl.__wdDyn = dyn;
    oldEl.__wdH = newEl.__wdH;
  }

  function patchChildren(parent, newNodes) {
    var i = 0;
    for (; i < newNodes.length; i++) {
      var nn = newNodes[i];
      var old = parent.childNodes[i];
      if (!old) { parent.appendChild(nn); continue; }
      if (old.nodeType === nn.nodeType && old.nodeType === 3) {
        if (old.data !== nn.data) old.data = nn.data;
      } else if (old.nodeType === 1 && nn.nodeType === 1 && old.localName === nn.localName && old.namespaceURI === nn.namespaceURI) {
        patchAttrs(old, nn);
        patchChildren(old, Array.prototype.slice.call(nn.childNodes));
      } else {
        parent.replaceChild(nn, old);
      }
    }
    while (parent.childNodes.length > i) parent.removeChild(parent.lastChild);
  }

  window.WD = {
    boot: function (Component, props) {
      var root = document.getElementById('wd-root');
      var tpl = document.getElementById('wd-tpl');
      if (!root || !tpl) return;
      var comp = new Component(props || {});
      var pending = false;
      var first = true;
      function draw() {
        pending = false;
        var vals = (comp.renderVals && comp.renderVals()) || {};
        var nodes = render(tpl.content.childNodes, vals, []);
        if (first) {
          // swap the prerendered copy for live nodes once
          first = false;
          while (root.firstChild) root.removeChild(root.firstChild);
          for (var i = 0; i < nodes.length; i++) root.appendChild(nodes[i]);
          return;
        }
        patchChildren(root, nodes);
      }
      comp.__schedule = function () {
        if (pending) return;
        pending = true;
        Promise.resolve().then(draw);
      };
      root.addEventListener('click', function (e) {
        var n = e.target;
        while (n && n !== root) {
          if (n.__wdH && n.__wdH.click) { n.__wdH.click(e); return; }
          n = n.parentNode;
        }
      });
      draw();
      if (comp.componentDidMount) comp.componentDidMount();
    }
  };
})();
