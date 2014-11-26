var myMessages = ['info','warning','error','success']; // define the messages types		 
function hideAllMessages()
{
		 var messagesHeights = new Array(); // this array will store height for each
	 
		 for (i=0; i<myMessages.length; i++)
		 {
				  messagesHeights[i] = $('.' + myMessages[i]).outerHeight();
				  $('.' + myMessages[i]).css('top', -messagesHeights[i]); //move element outside viewport	  
		 }
}

function showMessage(data,type)
{	
	$('.'+type+" p").html(data);
	  hideAllMessages();
	  
	  $('.'+type).animate({top:"0"}, 500);
	  setTimeout(hideAllMessages,3000);
}

$(document).ready(function(){
		 
		 // Initially, hide them all 
		 hideAllMessages();
		 // When message is clicked, hide it
		 $('.message').click(function(){			  
				  $(this).animate({top: -$(this).outerHeight()}, 500);
		  });		 	 
		 
			
});   

var clearIntervalTimers=[];
var clearTimeoutTimers=[];
(function() {
	  var proxied = $.unblockUI;
	  $.unblockUI = function() {
		  while( clearIntervalTimers.length>0){
			  clearInterval(clearIntervalTimers.pop());
		  }
		  while( clearTimeoutTimers.length>0){
			  clearTimeout(clearTimeoutTimers.pop());
		  }
		  
		 return proxied.apply(this, arguments);
	  };
	})();

var loadingScreen=function(msg,time,endMessage){
			var timerCount=0;
			var a=null;
			if(time>0){
				clearIntervalTimers.push(a=setInterval(function(){					
					$("#overlayMsg .counter").html((timerCount++)+"sec");
				},1000)
				);
				clearTimeoutTimers.push(
						setTimeout( function(){
							clearInterval(a);
							$("#overlayMsg").html(endMessage);
						} , time*1000)
					);
			}
	        $.blockUI({ message:"<div id='overlayMsg'> "+msg+ (time>0?"....<span class='counter'>0</span>":"")+"</div>" , css: { 
	            border: 'none', 
	            padding: '15px', 
	            backgroundColor: '#000', 
	            '-webkit-border-radius': '10px', 	
	            '-moz-border-radius': '10px', 
	            opacity: .5, 
	            color: '#fff' 
	        }});  
}

var removeLoadingScreen=function(msg){
	$.unblockUI();
}
