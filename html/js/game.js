var URL_TO_INTIIAL_SCREEN="./Login"

var game=null;
var n_primes=[19,59,5];
var tics=["mark1","mark2"];
var my_turn=false;
var _values=[];
var _filled=[];

var _valuesmain = [];
var _filledmain = [];

var _gridwin = [];
var enabled_grid=-1;

for(i=0;i<9;i++)_values.push([]);for(i=0;i<9;i++)for(j=0;j<9;j++)_values[i].push(5); 
for(i=0;i<9;i++)_filled.push([]);for(i=0;i<9;i++)for(j=0;j<9;j++)_filled[i].push(0); 

for(i=0;i<9;i++) _valuesmain.push(5);
for(i=0;i<9;i++) _filledmain.push(0);
for(i=0;i<9;i++) _gridwin.push(0);

var restart_game=null;

var setPoolId=function(id){
	pool_id=id;
}
var getPoolId=function(){
	return pool_id;
}
var highlight_grid=function(a,b,n){
	var i=0;
	if(b<=2){
		// row color
		for(i=0;i<3;i++)
			$("#"+[a,b*3+i].join("-")).css("background-color",n==0?"green":"red");
	}
	else if(b>=3 && b<=5){
		// row color
		for(i=0;i<3;i++)
			$("#"+[a,i*3+(b-3)].join("-")).css("background-color",n==0?"green":"red");
	}
	else if(b==6){
		// row color
			$("#"+a+"-"+0).css("background-color",n==0?"green":"red");
			$("#"+a+"-"+4).css("background-color",n==0?"green":"red");
			$("#"+a+"-"+8).css("background-color",n==0?"green":"red");
	}
	else if(b==7){
		$("#"+a+"-"+2).css("background-color",n==0?"green":"red");
		$("#"+a+"-"+4).css("background-color",n==0?"green":"red");
		$("#"+a+"-"+6).css("background-color",n==0?"green":"red");				
	}
}

var evaluate_main_grid = function()
{
// main win condition
	
	var sum_main=[0,0,0,0,0,0,0,0];
	var i=0,j=0;
	for(i=0;i<3;i++) for(j=0;j<3;j++) sum_main[i]+=_valuesmain[i*3+j]; //row sums
	for(i=0;i<3;i++) for(j=0;j<3;j++) sum_main[3+i]+=_valuesmain[j*3+i]; //row sums
	sum_main[6] = _valuesmain[0] + _valuesmain[4] + _valuesmain[8];
	sum_main[7] = _valuesmain[2] + _valuesmain[4] + _valuesmain[6];
	
	for(i=0;i<8;i++){
		if(sum_main[i]%n_primes[0]==0){ 
			
			$.post("./update_game/"+game["game_session"],"i=-2",function(data){
				for(var i=0;i<data["updates"].length;i++)
					update_game(data["updates"][i]);		
			}).fail(function(){
				
			});

			loadingScreen("You Win..",10,"<script>window.location.href='"+URL_TO_INTIIAL_SCREEN+"'</script>");
		}
		if(sum_main[i]%n_primes[1]==0){
			loadingScreen("You Loose..",10,"<script>window.location.href='"+URL_TO_INTIIAL_SCREEN+"'</script>");
		}
	}
}

var evaluate_small_grid=function(a){
	
	// sum array
	var sum_arr=[0,0,0,0,0,0,0,0];
	var i=0,j=0;
	for(i=0;i<3;i++) for(j=0;j<3;j++) sum_arr[i]+=_values[a][i*3+j]; //row sums
	for(i=0;i<3;i++) for(j=0;j<3;j++) sum_arr[3+i]+=_values[a][j*3+i]; //column sums
	sum_arr[6] = _values[a][0] + _values[a][4] + _values[a][8];//diagonal
	sum_arr[7] = _values[a][2] + _values[a][4] + _values[a][6];//diagonal
	
	// check sum
	
	if(_gridwin[a]==0){
	for(i=0;i<8;i++){
		if(sum_arr[i]%n_primes[0]==0){ 
			_valuesmain[a]=n_primes[0];
			_gridwin[a]=1;
			alert("You won grid number "+(a+1));
			highlight_grid(a,i,0);
			}
		if(sum_arr[i]%n_primes[1]==0){
			_valuesmain[a]=n_primes[1];
			alert("You lost grid number "+(a+1));
			highlight_grid(a,i,1);
			_gridwin[a]=1;
			}
	}
	}
	
	// check grid fill
	
	for(j=0;j<9;j++){
		if(_values[a][j]==5)
			break;
	}
	if(j==9) _filledmain[a] = 1;
	
	
	evaluate_main_grid();
}

var process_click=function (td,path){
	if(_filled[path[0]][path[1]]==1) {alert("Not possible");return;}
	if(!my_turn || $(td).attr("idx")!=undefined){ alert("It's not your move");return;}
	if(enabled_grid!=-1 && path[0]!=enabled_grid) {alert("Please choose a valid grid");return;}
	var index=0;
	console.log(path);
	for(var i=0;i<path.length;i++){
		index+=Math.pow(9,path.length-1-i)*(path[i]);
	}
	//update values
	_values[path[0]][path[1]]=n_primes[0];
	_filled[path[0]][path[1]]=1;
	
	evaluate_small_grid(path[0]);

	//add current cell updated cell 
	$(".current_cell").removeClass("current_cell");
	$(".current_grid").removeClass("current_grid");
	
	if(_filledmain[path[1]]==0) $("#"+path[1]).addClass("current_grid");
	else for(i=0;i<_filledmain.length;i++) if(_filledmain[i]==0) $("#"+i).addClass("current_grid");
	
	$(td).addClass(tics[0]).addClass("current_cell");
	
	$.post("./update_game/"+game["game_session"],"i="+index,function(data){
		for(var i=0;i<data["updates"].length;i++)
			update_game(data["updates"][i]);		
	}).fail(function(){setTimeut(reconnect,1000);});
}

var update_game=function(msg){
	var arr=null;
	var i=0;
	if((arr=/update.*?(\d+)/.exec(msg)) && arr.length>0){
		var index=parseInt(arr[1]);		
		
		arr=[];
		do{
			arr.push(index%9);
			index=parseInt(index/9);
		}while(index/9);
		for(i=arr.length;i<2;i++) arr.push(0);
		
		arr.reverse();
		
		// update values
		_values[arr[0]][arr[1]]=n_primes[1];
		_filled[arr[0]][arr[1]]=1;
		// enabled grid for the next move
		if(_filledmain[arr[1]]==0) enabled_grid=arr[1];
		else enabled_grid=-1;
		
		
 		evaluate_small_grid(arr[0]);
	
		//add current cell updated cell 
 		$(".current_cell").removeClass("current_cell"); 		
 		$(".current_grid").removeClass("current_grid");
 		
		if(_filledmain[arr[1]]==0) $("#"+arr[1]).addClass("current_grid");
		else for(i=0;i<_filledmain.length;i++) if(_filledmain[i]==0) $("#"+i).addClass("current_grid");

		//access table cell by id
		$("#"+arr.join("-")).addClass(tics[1]).addClass("current_cell").attr("idx",tics[1]);
		//check if game is won		
	}
	else if((arr=/your move/.exec(msg)) && arr.length>0){
		setUserTurn(true);
		reconnect();//keep a waiting connection to check if other user closes any connection
	}
	else if((arr=/^wait/.exec(msg)) && arr.length>0){
		//fallback here and resend
		setUserTurn(false);
	}
	
	else if((arr=/moved/.exec(msg)) && arr.length>0){
		//fallback here and resend
	}
	else if((arr=/reconnect/.exec(msg)) && arr.length>0){
		reconnect();
	}
	else if((arr=/hold on/.exec(msg)) && arr.length>0){
		alert("Please wait for your turn");
	}
	else if((arr=/connection_closed/.exec(msg)) && arr.length>0){
		alert("error the other player left the game , so reloadddd");
	}
	else if((arr=/player gone/.exec(msg)) && arr.length>0){
		//alert("Player not reachable wait for max 1 Min");		
		//setTimeOut();
		loadingScreen("waiting for user",60,"Player not found. <a href='"+URL_TO_INTIIAL_SCREEN+"'>click here to go back</a>");
		
	}
	else if((arr=/player in/.exec(msg)) && arr.length>0){
		//alert("Player reconnected");
		removeLoadingScreen();
		//cancel time out using the restart_game global flag
	}
	else if((arr=/restart/.exec(msg)) && arr.length>0){
		alert("Restarting ......");
		window.location.href=URL_TO_INTIIAL_SCREEN+"?message=Session Destroyed User Unavailable";
	}
	
	else if((arr=/done/.exec(msg)) && arr.length>0){
		loadingScreen("<h1><a href='"+URL_TO_INTIIAL_SCREEN+"'>Play Another Game</a></h1> ");
	}
	else if((arr=/error/.exec(msg)) && arr.length>0){
		loadingScreen("<h1><a href='"+URL_TO_INTIIAL_SCREEN+"'>Unable to Process</a></h1> ");
	}
}

var reconnect=function(){
		$("#debuginfo").append("<p>Waiting for reponse from partner...</p>");	
		$.post("./update_game/"+game["game_session"],{i:"-1"},function(data){
			
			for(var i=0;i<data["updates"].length;i++)
				update_game(data["updates"][i]);	
			}).fail(function(){setTimeout(reconnect,1000);});
}

var init_game=function(){
	$("#debuginfo").append("<p>Waiting for partner in pool:"+getPoolId()+"</p>");
	loadingScreen("Waiting for a user...",60,"<script>window.location.href='"+URL_TO_INTIIAL_SCREEN+"';</script>");
	
	$.post("./init_game?pool_id="+getPoolId(),function(data){
		game=data;		
		if("exit" in game){
			window.location.href=URL_TO_INTIIAL_SCREEN;
			return;
		}
		if(game["my_move"]=="false"){			
			reconnect();
			tics=["mark1","mark2"];
			n_primes=[19,59];			
		}
		else{
			$("#debuginfo").append("<p>It's your turn !! Make a move !!</p>");
			alert("It's your turn !! Make a move !!");
			tics=["mark2","mark1"];
			setUserTurn(true);
			n_primes=[59,19];
		}
		//ui code
		removeLoadingScreen();
		$("#uid1_name").html(game["users"][0]);
		$("#uid2_name").html(game["users"][1]);
		
		$("#uid1").attr("src","http://graph.facebook.com/"+game["users"][0]+"/picture");
		$("#uid2").attr("src","http://graph.facebook.com/"+game["users"][1]+"/picture");				
		$("#uid1_link").attr("href","http://www.facebook.com/"+game["users"][0]);
		$("#uid2_link").attr("src","http://www.facebook.com/"+game["users"][1]);				
	}).fail(function(){setTimeout(init_game,1000);});
}

var setUserTurn=function(turn){
	my_turn= turn;
	if(turn){
		$("#uid1_name").parent().addClass("activePlayer")
		$("#uid2_name").parent().removeClass("activPlayer");;//html(game["users"][1]+"(has to move..)");		
	}
	else{
		$("#uid1_name").parent().removeClass("activPlayer");		
		$("#uid2_name").parent().addClass("activePlayer");//html(game["users"][1]+"(has to move..)");		
	}
}
var generate_grid=function (level,path){
		if(level<1) return $("");
		var table=$("<table class='tic_tac_level_"+level+"'></table>");
		for(var i=0;i<3;i++){
			var tr=$("<tr></tr>").appendTo(table);
			for(var j=0;j<3;j++){
				var path2=path.slice(0); path2.push(3*i+j);
				var td=$("<td></td>").appendTo(tr);
				td.attr('id',path2.join("-")).attr('f',0).attr('v',5);
				// path => 5 ,2 =>  5 box in leve1 1 and 2nd box in level 2 ..
				if(level<2) td.click(function(td,path){return function(){process_click(td,path);}}(td,path2));								
				path.push(3*i+j);
				td.append(generate_grid(level-1,path));
				path.pop()
			}
		}
		return table;
}

$(document).ready(function(){
	$("#wrapper").append(generate_grid(2,[]));
	init_game();	
	
	////////////////////////////////////////
	$.fn.preload = function() {
	    this.each(function(){
	        $('<img/>')[0].src = this;
	    });
	}
	$(['./html/images/x_1.png','./html/images/x_2.png']).preload();	
});
	
// utility functions
(function() {
	  var proxied = window.alert;
	  window.alert = function() {
		//Boxy.alert(arguments[0], null, {title: 'Info'});
		  showMessage(arguments[0],"info");
	    return null;//proxied.apply(this, arguments);
	  };
	})();
