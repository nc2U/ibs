import{u as i,a as _}from"./theme.a85adb5c.js";import{d as l,h as p,v as c,j as u,o as f,c as m,_ as b}from"./framework.7b6aaa93.js";const v=l({__name:"VPCarbonAds",props:{carbonAds:{}},setup(r){const{page:d}=i(),a=r.carbonAds,{isAsideEnabled:s}=_(),o=p();let n=!1;function t(){if(!n){n=!0;const e=document.createElement("script");e.id="_carbonads_js",e.src=`//cdn.carbonads.com/carbon.js?serve=${a.code}&placement=${a.placement}`,e.async=!0,o.value.appendChild(e)}}return c(()=>d.value.relativePath,()=>{var e;n&&s.value&&((e=window._carbonads)==null||e.refresh())}),a&&u(()=>{s.value?t():c(s,e=>e&&t())}),(e,h)=>(f(),m("div",{class:"VPCarbonAds",ref_key:"container",ref:o},null,512))}});const x=b(v,[["__scopeId","data-v-a2f5d256"]]);export{x as default};
