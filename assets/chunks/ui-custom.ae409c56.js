import{e as r,u as i,f as d,r as l,g as u,w as _,o as p,c as f}from"../app.2390af6d.js";const A=r({__name:"VPCarbonAds",setup(m){const{theme:o}=i(),n=o.value.carbonAds,{isAsideEnabled:s}=d(),a=l();let t=!1;function c(){if(!t){t=!0;const e=document.createElement("script");e.id="_carbonads_js",e.src=`//cdn.carbonads.com/carbon.js?serve=${n.code}&placement=${n.placement}`,e.async=!0,a.value.appendChild(e)}}return n&&u(()=>{s.value?c():_(s,e=>e&&c())}),(e,b)=>(p(),f("div",{class:"VPCarbonAds",ref_key:"container",ref:a},null,512))}});export{A as default};
