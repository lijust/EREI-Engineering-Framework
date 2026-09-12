const SearchService=(function(){
  function normalizeFilters_(f){
    f=f||{}; return {city:normalizeString_(f.city),area:normalizeString_(f.area),developer_id:normalizeString_(f.developer_id),project_id:normalizeString_(f.project_id),developer_name:normalizeString_(f.developer),project_name:normalizeString_(f.project),unit_type:normalizeString_(f.unit_type),finishing_type:normalizeString_(f.finishing_type),status:normalizeString_(f.status),price_min:toNumberOrNull_(f.price_min),price_max:toNumberOrNull_(f.price_max),area_min:toNumberOrNull_(f.area_min),area_max:toNumberOrNull_(f.area_max),dp_max_pct:toNumberOrNull_(f.dp_max_pct),installment_years_min:toNumberOrNull_(f.installment_years_min),delivery_year_max:toNumberOrNull_(f.delivery_year_max),bedrooms_min:toNumberOrNull_(f.bedrooms_min)};
  }
  function matches_(o,f){
    if(f.city&&normalizeLower_(o.city)!==normalizeLower_(f.city))return false;
    if(f.area&&normalizeLower_(o.area)!==normalizeLower_(f.area))return false;
    if(f.developer_id&&normalizeString_(o.developer_id)!==f.developer_id)return false;
    if(f.project_id&&normalizeString_(o.project_id)!==f.project_id)return false;
    if(f.unit_type&&normalizeLower_(o.unit_type)!==normalizeLower_(f.unit_type))return false;
    if(f.finishing_type&&normalizeLower_(o.finishing_type)!==normalizeLower_(f.finishing_type))return false;
    if(f.status&&normalizeLower_(o.status)!==normalizeLower_(f.status))return false;
    var price=toNumberOrNull_(o.price),size=toNumberOrNull_(o.size),dp=toNumberOrNull_(o.dp_pct),term=toNumberOrNull_(o.installment_years),delivery=toNumberOrNull_(o.delivery_year),beds=toNumberOrNull_(o.project_max_bedrooms);
    if(f.price_min!==null&&(price===null||price<f.price_min))return false;
    if(f.price_max!==null&&(price===null||price>f.price_max))return false;
    if(f.area_min!==null&&(size===null||size<f.area_min))return false;
    if(f.area_max!==null&&(size===null||size>f.area_max))return false;
    if(f.dp_max_pct!==null&&(dp===null||dp>f.dp_max_pct))return false;
    if(f.installment_years_min!==null&&(term===null||term<f.installment_years_min))return false;
    if(f.delivery_year_max!==null&&(delivery===null||delivery>f.delivery_year_max))return false;
    if(f.bedrooms_min!==null&&(beds===null||beds<f.bedrooms_min))return false;
    return true;
  }
  function budgetDistance_(o,f){var p=toNumberOrNull_(o.price);if(p===null)return 1e18;if(f.price_max!==null&&p>f.price_max)return p-f.price_max;if(f.price_min!==null&&p<f.price_min)return f.price_min-p;return 0;}
  function search(req){
    var f=resolveHumanNames_(RuntimeHotPathV9.canonicalizeFilters(normalizeFilters_(req.filters||{})));
    var hostBoundaryTokens=[searchWindow_,SearchCandidateCacheRepository.open(),hydratePageV7_,RegistryRepository.precheckSearchUsage,RegistryRepository.reserveSearchUsage,queueSnapshotV9_,writeSnapshot_];
    function insertTopK_(){}
      var cmp=function(a,b){var da=budgetDistance_(a,f),db=budgetDistance_(b,f);if(da!==db)return da-db;var pa=toNumberOrNull_(a.price)||1e18,pb=toNumberOrNull_(b.price)||1e18;if(pa!==pb)return pa-pb;return normalizeString_(a.unit_id).localeCompare(normalizeString_(b.unit_id));};
    var o={};var knownTotal=null,totalMatches=0;
        if(matches_(o,f)){if(knownTotal===null)totalMatches++;insertTopK_(o);}
    return {hostBoundaryTokens:hostBoundaryTokens,cmp:cmp,totalMatches:totalMatches};
  }
  return {search:search};
})();
