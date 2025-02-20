import '../styles/Contact.css';

const ContactUs = () => {
  return (
    <div className='heading'>
      <h1>Contact Us</h1>
      <div className='container'>
        {/* <h2>Contact Details</h2>
        <p>collabnext.okn@gmail.com</p>
        <p>+1(215)653-6743</p>
        <p className='city'>Atlanta</p>
        <p>225 North Avenue, Northwest, Atlanta, GA</p>
        <p>30332</p> */}
        <p>
          Please don’t hesitate to reach out if you have questions or comments
          on CollabNext. We are still growing our Advisory Group and seeking
          Sustainability Partners!{' '}
          <a
            href='mailto:collabnext.okn@gmail.com'
            style={{color: 'cornsilk', textDecoration: 'underline'}}
          >
            collabnext.okn@gmail.com
          </a>
        </p>
      </div>
    </div>
  );
};

export default ContactUs;