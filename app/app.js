function dec2dms(d,dir)
{
    return (d>0?dir[0]:dir[1]) + " " + Math.floor(Math.abs(d)) + "° " + Math.floor(Math.abs(d)%1*60) + "' " + Math.round( (Math.abs(d)%1*60)%1*60*100)/100+ "''";
}

var gdata = {};
var $map = null;
var $ws = null;
var $me = null;
var $view = new ol.View({center:ol.proj.fromLonLat([17.83389, 59.52377]),zoom:15,minZoom:11,maxZoom:17,constrainResolution:true});

function messageHandler(evt)
{
    data = JSON.parse(evt.data);

    $.each(data,function(key,val){
        gdata[key] = val;

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

    }
    );

    pos = ol.proj.fromLonLat([gdata.lon, gdata.lat]);
    $me.setPosition(pos);

    //$view.setCenter(pos);
    //$view.setZoom(Math.round(17-gdata.speed/5));
    //$view.setRotation( -(gdata.speed<1.5?gdata.target_track:gdata.track)/180*Math.PI ) ;


    $("g#rot").attr("transform","rotate("+ Math.round(gdata.rot) +")");
    $("g#steer").attr("transform","rotate("+ Math.round(gdata.steer) +")");
    $("g#track").attr("transform","rotate("+ Math.round(gdata.target_track-gdata.track) +")");
}

function connectWS() // call once, keeps websocket alive.
{
    console.log("connect...");
    $ws = new WebSocket("ws://"+ location.hostname +":80/ws");
    $ws.onmessage = messageHandler;
    $ws.onclose = (e) => {console.log("close");setTimeout(connectWS,2000)};
    $ws.onerror = (e) => {console.log("error");/*setTimeout(connectWS,1000)*/};
    $ws.onopen = (e) => console.log("connected");
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


    $("span#enable").on("click",function(){$ws.send(JSON.stringify({"enable":1-gdata.enable}));});
    $("span#m_enable").on("click",function(){$ws.send(JSON.stringify({"m_enable":1-gdata.m_enable}));});

    $("div#pi_input input").on("change",function(e){
        $i = $(e.target);
        $o = {};
        $o[$i.attr("id")] = Number($i.val());
        $ws.send(JSON.stringify($o));
    });


    $("span#time").on("click",function(){
        $("#qr").toggleClass("visually-hidden");
        $("#ctrl").toggleClass("visually-hidden");
        $("#map").toggleClass("visually-hidden");
    });

    $("#ctrl button").on("click",function(id){
        var q = $(id.currentTarget).attr("q");
        $ws.send(JSON.stringify({'add': Number(q)}));
    });
});

