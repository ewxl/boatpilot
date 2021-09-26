function dec2dms(d,dir)
{
    return (d>0?dir[0]:dir[1]) + " " + Math.floor(Math.abs(d)) + "° " + Math.floor(Math.abs(d)%1*60) + "' " + Math.round( (Math.abs(d)%1*60)%1*60*100)/100+ "''";
}

var gdata = {};
var $map = null;
var $ws = null;
var $me = null;
var $view = new ol.View({center:ol.proj.fromLonLat([17.83389, 59.52377]),zoom:15,minZoom:11,maxZoom:17,constrainResolution:true});

function send(msg)
{
    o = {}
    o[msg] = ""
    $ws.send(JSON.stringify(o))
}

function set(key,val=undefined)
{
    o = {}
    o["set"] = val===undefined?key:{[key]:val}

    console.log(key,val,JSON.stringify(o))
    $ws.send(JSON.stringify(o))
}

pi_input = "Tp Ti Sp Si".split(" ")

function messageHandler(evt)
{
    data = JSON.parse(evt.data);
    console.log(data)
    $.each(data,function(key,val){
        gdata[key] = val;

        if(pi_input.indexOf(key)>=0)
        {
            if($(`div#pi_input input#${key}`).length==0)
                $(`<div class="input-group mb-3">
                  <div class="input-group-prepend">
                    <span class="input-group-text" id="basic-addon1">${key}</span>
                  </div>
                  <input type="text" id="${key}" class="form-control" placeholder="" aria-label="" aria-describedby="basic-addon1">
                </div>`).appendTo($("div#pi_input")).find("input").change(function(){set(key,Number($(this).val()))})

            $(`div#pi_input input#${key}`).attr("value",val)
        }

        if(key=="lon")
            val = dec2dms(val,"EW");

        if(key=="lat")
            val = dec2dms(val,"NS");

        if(key=="enable")
        {
            if(val)
            {
                $("span#enable").addClass("bg-success");
                $("div#pi_input").addClass("visually-hidden");
            }else{
                $("span#enable").removeClass("bg-success");
                $("div#pi_input").removeClass("visually-hidden");
            }
        }

        if(key=="m_enable")
        {
            if(val)
            {
                $("span#m_enable").addClass("bg-success");
            }else{
                $("span#m_enable").removeClass("bg-success");
            }
        }

        $("span#"+key).text(key+": "+val);
        $("input#"+key).val(val);

        if(key=="heading")
            $("g#heading").attr("transform",`rotate(${ Math.round(val) })`)

        if(key=="steeringwheel")
            $("g#steeringwheel").attr("transform",`rotate(${ Math.round(val*135) })`)

        if(key=="track_target")
            $("g#track_target").attr("transform",`rotate(${ Math.round(val) })`)


    }
    );

    pos = ol.proj.fromLonLat([gdata.lon, gdata.lat]);
    $me.setPosition(pos);

    $view.setCenter(pos);
    /*
    $view.setZoom(Math.round(17-gdata.speed/5));
    $view.setRotation( -(gdata.speed<1.5?gdata.target_track:gdata.track)/180*Math.PI );
*/

    if("lx" in data && "ly" in data)
        $("g#ps3dotl").attr("transform",`translate(${75+gdata.lx*75} ${75-gdata.ly*75})`)

    if("rx" in data && "ry" in data)
        $("g#ps3dotr").attr("transform",`translate(${75+data.rx*75} ${75-data.ry*75})`)

}

function connectWS() // call once, keeps websocket alive.
{
    console.log("connect...");
    $ws = new WebSocket("ws://"+ location.hostname +":80/ws");
    $ws.onmessage = messageHandler;
    $ws.onclose = (e) => {console.log("close");setTimeout(connectWS,2000)};
    $ws.onerror = (e) => {console.log("error");/*setTimeout(connectWS,1000)*/};
    $ws.onopen = (e) => {console.log("connected"),send("ping")};
}

$(document).ready(function(){
    connectWS();

    //setup map
    $map = new ol.Map({
        target: 'map',
        layers: [
            new ol.layer.Tile({
                source: new ol.source.XYZ(
                    {
                        //url:"https://map0{1-4}.eniro.com/geowebcache/service/tms1.0.0/nautical2x/{z}/{x}/{-y}.png" //?v=20210507"
                        url:"https://map0{1-4}.eniro.com/geowebcache/service/tms1.0.0/hydrographica2x/{z}/{x}/{-y}.png" //?v=20210507"

                        //nautical2x, hydrographica2x, nautical_hybrid2x, aerial (maxZoom: 20), map2x, hydrographica_hybrid2x
                        ,maxZoom:17,minZoom:11})
            }),
        ],
        view: $view,
    });

    $me = new ol.Overlay(
        {
            position: ol.proj.fromLonLat([0,0]),
            positioning: "center-center",
            element: document.getElementById("marker2")
        });


    $map.addOverlay($me);

    $("span#enable").on("click",()=>{set("enable",1-gdata.enable)});
    //$("span#m_enable").on("click",function(){$ws.send(JSON.stringify({"m_enable":1-gdata.m_enable}));});

    $("div#pi_input input").on("change",function(e){
        $i = $(e.target);
        $o = {};
        $o[$i.attr("id")] = Number($i.val());
        $ws.send(JSON.stringify($o));
    });


    $("span#time").click(()=>{
        $("#qr").toggleClass("visually-hidden");
        $("#ctrl").toggleClass("visually-hidden");
        $("#map").toggleClass("visually-hidden");
    });

    $("#ctrl button").click(function(){
        var q = $(this).attr("q");
        set('track_target',gdata.track_target+Number(q));
    });
});

