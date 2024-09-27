import '../styles/Contact.css';

const ContactUs = () => {
  return (
    <div className='heading'>

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
  );
};

export default ContactUs;
